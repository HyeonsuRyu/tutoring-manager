"""FR-ACC-02: email verification required before API login."""

import pytest
from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from django.test import override_settings
from django.urls import reverse


@pytest.mark.integration
@override_settings(ACCOUNT_EMAIL_VERIFICATION="mandatory")
def test_jwt_rejects_unverified_email(api_client, user):
    EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)
    res = api_client.post(
        "/api/v1/auth/token/",
        {"email": user.email, "password": "testpass123"},
        format="json",
    )
    assert res.status_code in (400, 401)
    assert "email" in str(res.data).lower() or "verified" in str(res.data).lower()


@pytest.mark.integration
@override_settings(ACCOUNT_EMAIL_VERIFICATION="mandatory")
def test_jwt_allows_verified_email(api_client, user):
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    res = api_client.post(
        "/api/v1/auth/token/",
        {"email": user.email, "password": "testpass123"},
        format="json",
    )
    assert res.status_code == 200
    assert "access" in res.data


@pytest.mark.integration
def test_signup_sends_verification_when_mandatory(web_client, mailoutbox):
    with override_settings(ACCOUNT_EMAIL_VERIFICATION="mandatory"):
        res = web_client.post(
            "/accounts/signup/",
            {
                "email": "verify-me@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
    assert res.status_code in (200, 302)
    assert len(mailoutbox) >= 1 or res.url.endswith("confirm-email") or "confirm" in (res.url or "")


@pytest.mark.integration
@override_settings(ACCOUNT_EMAIL_VERIFICATION="mandatory")
def test_signup_email_link_not_followed_by_korean_particle(web_client, mailoutbox):
    web_client.post(
        "/accounts/signup/",
        {
            "email": "particle-test@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        },
    )
    assert len(mailoutbox) == 1
    body = mailoutbox[0].body
    assert "/을" not in body
    assert "을 클릭" not in body


@pytest.mark.integration
def test_confirm_email_accepts_trailing_korean_particle_segment(web_client, user):
    address = EmailAddress.objects.create(
        user=user, email=user.email, verified=False, primary=True
    )
    confirmation = EmailConfirmationHMAC.create(address)
    base = reverse("account_confirm_email", kwargs={"key": confirmation.key})
    res = web_client.get(base + "%EC%9D%84/")
    assert res.status_code == 200
