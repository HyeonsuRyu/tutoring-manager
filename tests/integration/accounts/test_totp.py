"""FR-ACC-08: 2FA setup and sensitive pages (no TOTP enabled)."""

import pytest
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import BackupCode
from accounts.views_2fa import BACKUP_CODES_SESSION_KEY


@pytest.mark.integration
def test_totp_setup_page_when_logged_in(logged_in_client):
    res = logged_in_client.get("/accounts/2fa/setup/")
    assert res.status_code == 200
    assert "2단계" in res.content.decode() or "인증" in res.content.decode()


@pytest.mark.integration
def test_backup_codes_hidden_when_2fa_already_active(logged_in_client, user):
    TOTPDevice.objects.create(user=user, name="default", confirmed=True)
    BackupCode.objects.create(user=user, code="deadbeef", used=False)
    res = logged_in_client.get("/accounts/2fa/setup/")
    html = res.content.decode()
    assert "deadbeef" not in html
    assert "백업 코드" not in html


@pytest.mark.integration
def test_backup_codes_shown_once_from_session_flash(logged_in_client):
    session = logged_in_client.session
    session[BACKUP_CODES_SESSION_KEY] = ["flashcode01", "flashcode02"]
    session.save()
    res1 = logged_in_client.get("/accounts/2fa/setup/")
    html1 = res1.content.decode()
    assert "flashcode01" in html1
    assert "이번에만" in html1
    res2 = logged_in_client.get("/accounts/2fa/setup/")
    assert "flashcode01" not in res2.content.decode()


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
