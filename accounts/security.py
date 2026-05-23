"""Second-factor verification for sensitive actions."""

from __future__ import annotations

import time
from typing import Protocol

from django.contrib import messages
from django.shortcuts import redirect
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice

SENSITIVE_VERIFIED_SESSION_KEY = "sensitive_action_verified_at"
SENSITIVE_PENDING_POST_KEY = "sensitive_action_pending_post"
SENSITIVE_VERIFIED_TTL_SECONDS = 15 * 60


class SecondFactorBackend(Protocol):
    def verify(self, request, user) -> bool: ...


class TotpBackend:
    def verify(self, request, user) -> bool:
        token = (request.POST.get("otp_token") or request.POST.get("token") or "").strip()
        if not token:
            return False
        for device in devices_for_user(user):
            if isinstance(device, TOTPDevice) and device.verify_token(token):
                return True
        from accounts.backup_codes import verify_backup_code

        if verify_backup_code(user, token):
            return True
        return False


class WebAuthnBackend:
    def verify(self, request, user) -> bool:
        raise NotImplementedError("WebAuthn is not implemented yet")


WEBAUTHN_ENABLED = False


def user_has_totp(user) -> bool:
    return any(isinstance(d, TOTPDevice) for d in devices_for_user(user))


def verify_sensitive_action(request, user) -> bool:
    if not user_has_totp(user):
        return True
    backends: list[SecondFactorBackend] = [TotpBackend()]
    if WEBAUTHN_ENABLED:
        backends.append(WebAuthnBackend())
    return any(b.verify(request, user) for b in backends)


def _is_sensitive_verified(request) -> bool:
    verified_at = request.session.get(SENSITIVE_VERIFIED_SESSION_KEY)
    if not verified_at:
        return False
    if time.time() - float(verified_at) > SENSITIVE_VERIFIED_TTL_SECONDS:
        request.session.pop(SENSITIVE_VERIFIED_SESSION_KEY, None)
        return False
    return True


def _mark_sensitive_verified(request) -> None:
    request.session[SENSITIVE_VERIFIED_SESSION_KEY] = time.time()
    request.session.modified = True


def _stash_pending_post(request) -> None:
    data: dict[str, str | list[str]] = {}
    for key in request.POST:
        if key in ("csrfmiddlewaretoken", "otp_token"):
            continue
        values = request.POST.getlist(key)
        data[key] = values if len(values) > 1 else values[0]
    if data:
        request.session[SENSITIVE_PENDING_POST_KEY] = data
        request.session.modified = True


def _merge_pending_post(request) -> None:
    pending = request.session.get(SENSITIVE_PENDING_POST_KEY)
    if not pending or request.method != "POST":
        return
    merged = request.POST.copy()
    for key, value in pending.items():
        if key in ("csrfmiddlewaretoken", "otp_token"):
            continue
        if key in merged:
            continue
        if isinstance(value, list):
            merged.setlist(key, value)
        else:
            merged[key] = value
    request.POST = merged


def _post_has_business_fields(request) -> bool:
    skip = {"csrfmiddlewaretoken", "otp_token"}
    return any(k for k in request.POST if k not in skip)


class SensitiveActionMixin:
    """Require TOTP re-auth when user has 2FA enabled."""

    def dispatch(self, request, *args, **kwargs):
        if not user_has_totp(request.user):
            return super().dispatch(request, *args, **kwargs)

        if request.method == "POST":
            _merge_pending_post(request)

        if _is_sensitive_verified(request):
            return super().dispatch(request, *args, **kwargs)

        otp_token = (request.POST.get("otp_token") or "").strip()
        if request.method == "POST" and otp_token:
            if verify_sensitive_action(request, request.user):
                _mark_sensitive_verified(request)
                request.session.pop(SENSITIVE_PENDING_POST_KEY, None)
                if not _post_has_business_fields(request):
                    return redirect(request.path)
                return super().dispatch(request, *args, **kwargs)
            messages.error(request, "인증 코드가 올바르지 않습니다.")
            return self.render_totp_challenge(request)

        if request.method == "POST":
            _stash_pending_post(request)

        return self.render_totp_challenge(request)

    def render_totp_challenge(self, request):
        from django.shortcuts import render

        return render(request, "accounts/totp_challenge.html", {"title": "2단계 인증"})
