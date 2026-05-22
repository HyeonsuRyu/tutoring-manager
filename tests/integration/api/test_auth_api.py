"""FR-MOB-02, FR-ACC-09: JWT authentication API."""


def test_token_obtain_with_email(api_client, user):
    res = api_client.post(
        "/api/v1/auth/token/",
        {"email": user.email, "password": "testpass123"},
        format="json",
    )
    assert res.status_code == 200
    assert "access" in res.data
    assert "refresh" in res.data


def test_token_reject_wrong_password(api_client, user):
    res = api_client.post(
        "/api/v1/auth/token/",
        {"email": user.email, "password": "wrong"},
        format="json",
    )
    assert res.status_code == 401


def test_protected_endpoint_requires_auth(api_client):
    res = api_client.get("/api/v1/students/")
    assert res.status_code in (401, 403, 404)
