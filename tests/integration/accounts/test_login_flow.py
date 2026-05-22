"""FR-ACC-03, ACC-05, ACC-06: web login and access control."""

import pytest
from django.urls import reverse


@pytest.mark.integration
def test_login_page_renders(web_client):
    res = web_client.get("/accounts/login/")
    assert res.status_code == 200
    assert "로그인" in res.content.decode()


@pytest.mark.integration
def test_login_with_email_redirects_home(web_client, user):
    res = web_client.post(
        "/accounts/login/",
        {"login": user.email, "password": "testpass123"},
    )
    assert res.status_code == 302
    assert res.url == reverse("home")


@pytest.mark.integration
def test_wrong_password_stays_on_login(web_client, user):
    res = web_client.post(
        "/accounts/login/",
        {"login": user.email, "password": "wrong"},
    )
    assert res.status_code == 200


@pytest.mark.integration
def test_anonymous_redirected_from_home(web_client):
    res = web_client.get("/")
    assert res.status_code == 302
    assert "/accounts/login" in res.url


@pytest.mark.integration
def test_anonymous_redirected_from_students(web_client):
    res = web_client.get("/students/")
    assert res.status_code == 302
    assert "/accounts/login" in res.url
