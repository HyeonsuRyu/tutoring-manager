"""FR-ACC-01: public signup page (allauth)."""

import pytest


@pytest.mark.integration
def test_signup_page_renders(client):
    response = client.get("/accounts/signup/", HTTP_HOST="127.0.0.1")
    assert response.status_code == 200
    content = response.content.decode()
    assert "회원가입" in content
    assert 'name="email"' in content or "email" in content.lower()


@pytest.mark.integration
def test_signup_creates_user(client, mailoutbox):
    response = client.post(
        "/accounts/signup/",
        {
            "email": "new@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        },
        HTTP_HOST="127.0.0.1",
    )
    assert response.status_code in (200, 302)
    from accounts.models import User

    assert User.objects.filter(email="new@example.com").exists()


@pytest.mark.integration
def test_signup_duplicate_email_shows_error(web_client, user):
    res = web_client.post(
        "/accounts/signup/",
        {
            "email": user.email,
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        },
    )
    assert res.status_code == 200
    assert "이미" in res.content.decode() or "already" in res.content.decode().lower()
