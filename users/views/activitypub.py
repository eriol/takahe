import json

from asgiref.sync import async_to_sync
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from activities.models import Post
from core import exceptions
from core.ld import canonicalise
from core.models import Config
from core.signatures import (
    HttpSignature,
    LDSignature,
    VerificationError,
    VerificationFormatError,
)
from takahe import __version__
from users.models import Identity, InboxMessage, SystemActor
from users.shortcuts import by_handle_or_404


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401


class HostMeta(View):
    """
    Returns a canned host-meta response
    """

    def get(self, request):
        return HttpResponse(
            """<?xml version="1.0" encoding="UTF-8"?>
            <XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">
            <Link rel="lrdd" template="https://%s/.well-known/webfinger?resource={uri}"/>
            </XRD>"""
            % request.META["HTTP_HOST"],
            content_type="application/xml",
        )


class NodeInfo(View):
    """
    Returns the well-known nodeinfo response, pointing to the 2.0 one
    """

    def get(self, request):
        host = request.META.get("HOST", settings.MAIN_DOMAIN)
        return JsonResponse(
            {
                "links": [
                    {
                        "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                        "href": f"https://{host}/nodeinfo/2.0/",
                    }
                ]
            }
        )


class NodeInfo2(View):
    """
    Returns the nodeinfo 2.0 response
    """

    def get(self, request):
        # Fetch some user stats
        local_identities = Identity.objects.filter(local=True).count()
        local_posts = Post.objects.filter(local=True).count()
        return JsonResponse(
            {
                "version": "2.0",
                "software": {"name": "takahe", "version": __version__},
                "protocols": ["activitypub"],
                "services": {"outbound": [], "inbound": []},
                "usage": {
                    "users": {"total": local_identities},
                    "localPosts": local_posts,
                },
                "openRegistrations": Config.system.signup_allowed
                and not Config.system.signup_invite_only,
                "metadata": {},
            }
        )


class Webfinger(View):
    """
    Services webfinger requests
    """

    def get(self, request):
        resource = request.GET.get("resource")
        if not resource:
            return HttpResponseBadRequest("No resource specified")
        if not resource.startswith("acct:"):
            return HttpResponseBadRequest("Not an account resource")
        handle = resource[5:]

        if handle.startswith("__system__@"):
            # They are trying to webfinger the system actor
            actor = SystemActor()
        else:
            actor = by_handle_or_404(request, handle)
            handle = actor.handle

        return JsonResponse(
            {
                "subject": f"acct:{handle}",
                "aliases": [
                    actor.absolute_profile_uri(),
                ],
                "links": [
                    {
                        "rel": "http://webfinger.net/rel/profile-page",
                        "type": "text/html",
                        "href": actor.absolute_profile_uri(),
                    },
                    {
                        "rel": "self",
                        "type": "application/activity+json",
                        "href": actor.actor_uri,
                    },
                ],
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class Inbox(View):
    """
    AP Inbox endpoint
    """

    def post(self, request, handle):
        # Load the LD
        document = canonicalise(json.loads(request.body), include_security=True)
        # Find the Identity by the actor on the incoming item
        # This ensures that the signature used for the headers matches the actor
        # described in the payload.
        identity = Identity.by_actor_uri(document["actor"], create=True, transient=True)
        if not identity.public_key:
            # See if we can fetch it right now
            async_to_sync(identity.fetch_actor)()
        if not identity.public_key:
            exceptions.capture_message(
                f"Inbox error: cannot fetch actor {document['actor']}"
            )
            return HttpResponseBadRequest("Cannot retrieve actor")
        # See if it's from a blocked domain
        if identity.domain.blocked:
            # I love to lie! Throw it away!
            exceptions.capture_message(
                f"Inbox: Discarded message from {identity.domain}"
            )
            return HttpResponse(status=202)
        # If there's a "signature" payload, verify against that
        if "signature" in document:
            try:
                LDSignature.verify_signature(document, identity.public_key)
            except VerificationFormatError as e:
                exceptions.capture_message(
                    f"Inbox error: Bad LD signature format: {e.args[0]}"
                )
                return HttpResponseBadRequest(e.args[0])
            except VerificationError:
                exceptions.capture_message("Inbox error: Bad LD signature")
                return HttpResponseUnauthorized("Bad signature")
        # Otherwise, verify against the header (assuming it's the same actor)
        else:
            try:
                HttpSignature.verify_request(
                    request,
                    identity.public_key,
                )
            except VerificationFormatError as e:
                exceptions.capture_message(
                    f"Inbox error: Bad HTTP signature format: {e.args[0]}"
                )
                return HttpResponseBadRequest(e.args[0])
            except VerificationError:
                exceptions.capture_message("Inbox error: Bad HTTP signature")
                return HttpResponseUnauthorized("Bad signature")
        # Hand off the item to be processed by the queue
        InboxMessage.objects.create(message=document)
        return HttpResponse(status=202)


class SystemActorView(View):
    """
    Special endpoint for the overall system actor
    """

    def get(self, request):
        return JsonResponse(
            canonicalise(
                SystemActor().to_ap(),
                include_security=True,
            )
        )
