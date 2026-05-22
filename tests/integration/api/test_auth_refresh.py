"""FR-MOB-04: JWT refresh token."""

import pytest


@pytest.mark.integration
@pytest.mark.api
def test_token_refresh_returns_new_access(api_client, user):
    login = api_client.post(
        "/api/v1/auth/token/",
        {"email": user.email, "password": "testpass123"},
        format="json",
    )
    assert login.status_code == 200
    refresh = login.data["refresh"]
    res = api_client.post("/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json")
    assert res.status_code == 200
    assert "access" in res.data
