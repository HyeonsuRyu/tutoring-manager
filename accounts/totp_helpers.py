"""TOTP setup context and activation (shared by account settings)."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.backup_codes import generate_backup_codes

BACKUP_CODES_SESSION_KEY = "totp_backup_codes_reveal"


def get_totp_setup_context(request: HttpRequest) -> dict:
    device, _created = TOTPDevice.objects.get_or_create(
        user=request.user, name="default", defaults={"confirmed": False}
    )
    if not device.confirmed:
        device.save()
    backup_codes = request.session.pop(BACKUP_CODES_SESSION_KEY, None) or []
    return {
        "config_url": device.config_url,
        "device": device,
        "backup_codes": backup_codes,
    }


def activate_totp_device(request: HttpRequest, token: str) -> bool:
    """Confirm TOTP device; on first activation generate backup codes in session."""
    device = TOTPDevice.objects.filter(user=request.user, name="default").first()
    if not device or not device.verify_token(token):
        return False
    first_activation = not device.confirmed
    device.confirmed = True
    device.save()
    if first_activation:
        request.session[BACKUP_CODES_SESSION_KEY] = generate_backup_codes(request.user)
    messages.success(request, "2단계 인증이 활성화되었습니다.")
    return True
