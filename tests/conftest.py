import time

import pytest

from core.models import Config
from stator.runner import StatorModel, StatorRunner
from users.models import Domain, Identity, User


@pytest.fixture
def keypair():
    """
    Testing-only keypair
    """
    return {
        "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCzNJa9JIxQpOtQ
z8UQKXDPREF9DyBliGu3uPWo6DMnkOm7hoh2+nOryrWDqWOFaVK//n7kltHXUEbm
U3exh0/0iWfzx2AbNrI04csAvW/hRvHbHBnVTotSxzqTd3ESkpcSW4xVuz9aCcFR
kW3unSCO3fF0Lh8Jsy9N/CT6oTnwG+ZpeGvHVbh9xfR5Ww6zA7z8A6B17hbzdMd/
3qUPijyIb5se4cWVtGg/ZJ0X1syn9u9kpwUjhHlyWH/esMRHxPuW49BPZPhhKs1+
t//4xgZcRX515qFqPS2EtYgZAfh7M3TRv8uCSzL4TT+8ka9IUwKdV6TFaqH27bAG
KyJQfGaTAgMBAAECggEALZY5qFjlRtiFMfQApdlc5KTw4d7Yt2tqN3zaJUMYTD7d
boJNMbMJfNCetyT+d6Aw2D1ly0GglNzLhGkEQElzKfpQUt/Lj3CtCa3Mpd4K2Wxi
NwJhgfUulPqwaHYQchCPVLCsNNziw0VLA7Rymionb6B+/TaEV8PYy0ZSo90ir3UD
CL5t+IWgIPiy6pk1wGOmeB+tU4+V7/hFel+vPFNahafqVhLE311dfx2aOfweAEfN
e4JoPeJP1/fB+BVZMyVSAraKz6wheymBBNKKn/vpFsdd6it2AP4UZeFp6ma9wT9t
nk65IpHg1MBxazQd7621GrPH+ZnhMg62H/FEj6rIDQKBgQC1w1fEbk+zjI54DXU8
FAe5cJbZS89fMP5CtzlWKzTzfdaavT+5cUYp3XAv37tSGsqYAXxY+4bHGa+qdCQO
I41cmylWGNX2e29/p2BspDPM6YQ0Z21MxFRBTWvHFrhd0bF1cXKBKPttdkKvzOEP
6uNy+/QtRNn9xF/ZjaMHcyPPTQKBgQD8ZdOmZ3TMsYJchAjjseN8S+Objw2oZzmK
6I1ULJBz3DWiyCUfir+pMjSH4fsAf9zrHkiM7xUgMByTukVRt16BrT7TlEBanAxc
/AKdNB3f0pza829LCz1lMAUn+ngZLTmRR+1rQFXqTjhB+0peJzKiMli+9BBhL9Ry
jMeTuLHdXwKBgGiz9kL5KIBNX2RYnEfXYfu4l6zktrgnCNB1q1mv2fjJbG4GxkaU
sc47+Pwa7VUGid22PWMkwSa/7SlLbdmXMT8/QjiOZfJueHQYfrsWe6B2g+mMCrJG
BiL37jXpKJsiyA7XIxaz/OG5VgDfDGaW8B60dJv/JXPBQ1WW+Wq5MM+hAoGAAUdS
xykHAnJzwpw4n06rZFnOEV+sJgo/1GBRNvfy02NuMiDpbzt4tRa4BWgzqVD8gYRp
wa0EYmFcA7OR3lQbenSyOMgre0oHFgGA0eMNs7CRctqA2dR4vyZ7IDS4nwgHnqDK
pxxwUvuKdWsceVWhgAjZQj5iRtvDK8Fi0XDCFekCgYALTU1v5iMIpaRAe+eyA2B1
42qm4B/uhXznvOu2YXU6iJFmMgHGYgpa+Dq8uUjKtpn/LIFeX1KN0hH8z/0LW3gB
e7tN7taW0oLK3RQcEMfkZ7diE9x3LGqo/xMxsZMtxAr88p5eMEU/nxxznOqq+W9b
qxRbXYzEtHz+cW9+FZkyVw==
-----END PRIVATE KEY-----""",
        "public_key": """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAszSWvSSMUKTrUM/FEClw
z0RBfQ8gZYhrt7j1qOgzJ5Dpu4aIdvpzq8q1g6ljhWlSv/5+5JbR11BG5lN3sYdP
9Iln88dgGzayNOHLAL1v4Ubx2xwZ1U6LUsc6k3dxEpKXEluMVbs/WgnBUZFt7p0g
jt3xdC4fCbMvTfwk+qE58BvmaXhrx1W4fcX0eVsOswO8/AOgde4W83THf96lD4o8
iG+bHuHFlbRoP2SdF9bMp/bvZKcFI4R5clh/3rDER8T7luPQT2T4YSrNfrf/+MYG
XEV+deahaj0thLWIGQH4ezN00b/Lgksy+E0/vJGvSFMCnVekxWqh9u2wBisiUHxm
kwIDAQAB
-----END PUBLIC KEY-----""",
        "public_key_id": "https://example.com/test-actor#test-key",
    }


@pytest.fixture
def config_system(keypair):
    Config.system = Config.SystemOptions(
        system_actor_private_key=keypair["private_key"],
        system_actor_public_key=keypair["public_key"],
    )
    yield Config.system


@pytest.fixture
@pytest.mark.django_db
def user() -> User:
    return User.objects.create(email="test@example.com")


@pytest.fixture
@pytest.mark.django_db
def domain() -> Domain:
    return Domain.objects.create(domain="example.com", local=True, public=True)


@pytest.fixture
@pytest.mark.django_db
def identity(user, domain) -> Identity:
    """
    Creates a basic test identity with a user and domain.
    """
    identity = Identity.objects.create(
        actor_uri="https://example.com/@test@example.com/",
        username="test",
        domain=domain,
        name="Test User",
        local=True,
    )
    identity.users.set([user])
    return identity


@pytest.fixture
def other_identity(user, domain) -> Identity:
    """
    Creates a different basic test identity with a user and domain.
    """
    identity = Identity.objects.create(
        actor_uri="https://example.com/@other@example.com/",
        username="other",
        domain=domain,
        name="Other User",
        local=True,
    )
    identity.users.set([user])
    return identity


@pytest.fixture
@pytest.mark.django_db
def remote_identity() -> Identity:
    """
    Creates a basic remote test identity with a domain.
    """
    domain = Domain.objects.create(domain="remote.test", local=False)
    return Identity.objects.create(
        actor_uri="https://remote.test/test-actor/",
        profile_uri="https://remote.test/@test/",
        username="test",
        domain=domain,
        name="Test Remote User",
        local=False,
    )


@pytest.fixture
def stator_runner(config_system) -> StatorRunner:
    """
    Return an initialized StatorRunner for tests that need state transitioning
    to happen.

    Example:
        # Do some tasks with state side effects
        async_to_sync(stator_runner.fetch_and_process_tasks)()
    """
    runner = StatorRunner(
        StatorModel.subclasses,
        concurrency=100,
        schedule_interval=30,
    )
    runner.handled = 0
    runner.started = time.monotonic()
    runner.last_clean = time.monotonic() - runner.schedule_interval
    runner.tasks = []

    return runner
