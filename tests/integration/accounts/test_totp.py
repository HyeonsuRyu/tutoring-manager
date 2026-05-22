"""FR-ACC-08: 2FA setup and sensitive pages (no TOTP enabled)."""

import pytest


@pytest.mark.integration
def test_totp_setup_page_when_logged_in(logged_in_client):
    res = logged_in_client.get("/accounts/2fa/setup/")
    assert res.status_code == 200
    assert "2단계" in res.content.decode() or "인증" in res.content.decode()


@pytest.mark.integration
def test_password_change_page_when_logged_in(logged_in_client):
    res = logged_in_client.get("/accounts/password/change/")
    assert res.status_code == 200
    assert "app-shell" in res.content.decode()


@pytest.mark.integration
def test_email_page_when_logged_in(logged_in_client):
    res = logged_in_client.get("/accounts/email/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "app-shell" in html
    assert "등록된 이메일" in html
