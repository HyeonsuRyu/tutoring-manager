"""FR-ACC-08: 2FA setup and sensitive pages (no TOTP enabled)."""

import pytest
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import BackupCode
from accounts.totp_helpers import BACKUP_CODES_SESSION_KEY


@pytest.mark.integration
def test_account_settings_page_when_logged_in(logged_in_client):
    res = logged_in_client.get("/accounts/settings/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "계정 관리" in html
    assert "2단계 인증" in html
    assert "비밀번호" in html


def test_legacy_totp_setup_url_redirects_to_settings(logged_in_client):
    res = logged_in_client.get("/accounts/2fa/setup/", follow=False)
    assert res.status_code == 302
    assert res.url == "/accounts/settings/"


@pytest.mark.integration
def test_backup_codes_hidden_when_2fa_already_active(logged_in_client, user):
    TOTPDevice.objects.create(user=user, name="default", confirmed=True)
    row = BackupCode(user=user, used=False)
    row.set_code("deadbeef")
    row.save()
    res = logged_in_client.get("/accounts/settings/")
    html = res.content.decode()
    assert "deadbeef" not in html
    assert "backup-codes-reveal" not in html


@pytest.mark.integration
def test_backup_codes_shown_once_from_session_flash(logged_in_client):
    session = logged_in_client.session
    session[BACKUP_CODES_SESSION_KEY] = ["flashcode01", "flashcode02"]
    session.save()
    res1 = logged_in_client.get("/accounts/settings/")
    html1 = res1.content.decode()
    assert "flashcode01" in html1
    assert "이번에만" in html1
    res2 = logged_in_client.get("/accounts/settings/")
    assert "flashcode01" not in res2.content.decode()


@pytest.mark.integration
def test_backup_codes_stored_hashed_not_plaintext(user):
    from django.contrib.auth.hashers import identify_hasher

    from accounts.backup_codes import generate_backup_codes, verify_backup_code

    plain_codes = generate_backup_codes(user)
    plain = plain_codes[0]
    for row in BackupCode.objects.filter(user=user):
        assert plain not in row.code_hash
        identify_hasher(row.code_hash)
    assert verify_backup_code(user, plain) is True
    assert verify_backup_code(user, plain) is False


@pytest.mark.integration
def test_password_change_page_when_logged_in(logged_in_client):
    res = logged_in_client.get("/accounts/password/change/")
    assert res.status_code == 200
    assert "app-shell" in res.content.decode()


@pytest.mark.integration
def test_legacy_email_url_redirects_to_settings(logged_in_client):
    res = logged_in_client.get("/accounts/email/", follow=True)
    assert res.status_code == 200
    html = res.content.decode()
    assert "계정 관리" in html
