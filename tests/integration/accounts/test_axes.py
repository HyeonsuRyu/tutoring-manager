"""FR-ACC-07: django-axes login lockout."""

import pytest
from django.test import override_settings


@pytest.mark.integration
@override_settings(
    AXES_ENABLED=True,
    AXES_FAILURE_LIMIT=3,
    AXES_COOLOFF_TIME=1,
    AXES_LOCKOUT_PARAMETERS=["ip_address", "username"],
)
def test_axes_locks_after_repeated_failures(web_client, user):
    for _ in range(3):
        web_client.post(
            "/accounts/login/",
            {"login": user.email, "password": "wrong-password"},
        )
    res = web_client.post(
        "/accounts/login/",
        {"login": user.email, "password": "testpass123"},
    )
    # Locked users should not reach successful redirect to home
    assert res.status_code != 302 or "/accounts/login" in (res.url or "")
