"""SensitiveActionMixin session and pending POST handling (no DB)."""

import time
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.views import View

from accounts.security import (
    SENSITIVE_PENDING_POST_KEY,
    SENSITIVE_VERIFIED_SESSION_KEY,
    SENSITIVE_VERIFIED_TTL_SECONDS,
    SensitiveActionMixin,
    _is_sensitive_verified,
    _merge_pending_post,
)


class _SessionDict(dict):
    modified = False


def _with_session(request):
    request.session = _SessionDict()
    return request


@pytest.mark.unit
def test_merge_pending_post_restores_password_fields():
    factory = RequestFactory()
    request = _with_session(
        factory.post("/accounts/password/change/", {"otp_token": "123456", "csrfmiddlewaretoken": "x"})
    )
    request.session[SENSITIVE_PENDING_POST_KEY] = {
        "oldpassword": "old",
        "password1": "newpass123!",
        "password2": "newpass123!",
    }
    _merge_pending_post(request)
    assert request.POST["oldpassword"] == "old"
    assert request.POST["password1"] == "newpass123!"
    assert request.POST["otp_token"] == "123456"


@pytest.mark.unit
def test_sensitive_verified_expires():
    factory = RequestFactory()
    request = _with_session(factory.get("/accounts/email/"))
    request.session[SENSITIVE_VERIFIED_SESSION_KEY] = time.time() - SENSITIVE_VERIFIED_TTL_SECONDS - 1
    assert _is_sensitive_verified(request) is False


class _ProbeView(SensitiveActionMixin, View):
    def get(self, request):
        from django.http import HttpResponse

        return HttpResponse("ok-page")

    def post(self, request):
        from django.http import HttpResponse

        if request.POST.get("oldpassword"):
            return HttpResponse("password-changed")
        return HttpResponse("post-ok")


@pytest.mark.unit
@patch("accounts.security.user_has_totp", return_value=True)
@patch("accounts.security.verify_sensitive_action", return_value=True)
def test_otp_only_post_redirects_then_get_shows_page(_verify, _has_totp):
    factory = RequestFactory()
    view = _ProbeView.as_view()

    get_req = _with_session(factory.get("/accounts/email/"))
    get_req.user = AnonymousUser()
    challenge = view(get_req)
    assert challenge.status_code == 200
    assert "인증 앱" in challenge.content.decode()

    post_req = factory.post("/accounts/email/", {"otp_token": "123456"})
    post_req.user = get_req.user
    post_req.session = get_req.session
    redirect = view(post_req)
    assert redirect.status_code == 302
    assert redirect.url == "/accounts/email/"

    get2 = factory.get("/accounts/email/")
    get2.user = post_req.user
    get2.session = post_req.session
    res = view(get2)
    assert res.status_code == 200
    assert res.content == b"ok-page"


@pytest.mark.unit
@patch("accounts.security.user_has_totp", return_value=True)
@patch("accounts.security.verify_sensitive_action", return_value=True)
def test_password_post_with_pending_merged_after_otp(_verify, _has_totp):
    factory = RequestFactory()
    view = _ProbeView.as_view()

    request = _with_session(
        factory.post(
            "/accounts/password/change/",
            {
                "oldpassword": "old",
                "password1": "newpass123!",
                "password2": "newpass123!",
            },
        )
    )
    request.user = AnonymousUser()

    challenge = view(request)
    assert challenge.status_code == 200
    assert SENSITIVE_PENDING_POST_KEY in request.session

    otp_req = factory.post("/accounts/password/change/", {"otp_token": "123456"})
    otp_req.user = request.user
    otp_req.session = request.session
    res = view(otp_req)
    assert res.status_code == 200
    assert res.content == b"password-changed"
