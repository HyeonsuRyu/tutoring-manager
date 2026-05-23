"""Second-factor verification for sensitive actions."""

from __future__ import annotations

from typing import Protocol

from django.contrib import messages
from django.shortcuts import redirect
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice


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


class SensitiveActionMixin:
    """Require TOTP re-auth when user has 2FA enabled."""

    sensitive_session_key = "sensitive_action_verified"

    def dispatch(self, request, *args, **kwargs):
        if request.method in ("GET", "HEAD", "OPTIONS") and request.GET.get("otp_token"):
            request.POST = request.POST.copy()
            request.POST["otp_token"] = request.GET["otp_token"]
        if request.method == "POST" and not request.POST.get("otp_token"):
            if request.session.get(self.sensitive_session_key):
                return super().dispatch(request, *args, **kwargs)
        if user_has_totp(request.user) and not verify_sensitive_action(request, request.user):
            if request.method == "POST" and request.POST.get("otp_token"):
                messages.error(request, "인증 코드가 올바르지 않습니다.")
            return self.render_totp_challenge(request)
        request.session[self.sensitive_session_key] = True
        try:
            return super().dispatch(request, *args, **kwargs)
        finally:
            request.session.pop(self.sensitive_session_key, None)

    def render_totp_challenge(self, request):
        from django.shortcuts import render

        return render(request, "accounts/totp_challenge.html", {"title": "2단계 인증"})
