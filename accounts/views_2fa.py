import secrets

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import BackupCode
from accounts.security import user_has_totp

BACKUP_CODES_SESSION_KEY = "totp_backup_codes_reveal"
BACKUP_CODE_COUNT = 8


def generate_backup_codes(user) -> list[str]:
    BackupCode.objects.filter(user=user).delete()
    codes: list[str] = []
    for _ in range(BACKUP_CODE_COUNT):
        code = secrets.token_hex(4)
        BackupCode.objects.create(user=user, code=code)
        codes.append(code)
    return codes


class TotpSetupView(LoginRequiredMixin, View):
    template_name = "accounts/totp_setup.html"

    def get(self, request):
        device, _created = TOTPDevice.objects.get_or_create(
            user=request.user, name="default", defaults={"confirmed": False}
        )
        if not device.confirmed:
            device.save()
        backup_codes = request.session.pop(BACKUP_CODES_SESSION_KEY, None) or []
        return render(
            request,
            self.template_name,
            {"config_url": device.config_url, "device": device, "backup_codes": backup_codes},
        )

    def post(self, request):
        token = request.POST.get("token", "")
        device = TOTPDevice.objects.filter(user=request.user, name="default").first()
        if device and device.verify_token(token):
            first_activation = not device.confirmed
            device.confirmed = True
            device.save()
            if first_activation:
                request.session[BACKUP_CODES_SESSION_KEY] = generate_backup_codes(request.user)
            messages.success(request, "2단계 인증이 활성화되었습니다.")
            return redirect("totp-setup")
        messages.error(request, "코드가 올바르지 않습니다.")
        return redirect("totp-setup")


class TotpDisableView(LoginRequiredMixin, View):
    def post(self, request):
        from accounts.security import verify_sensitive_action

        if user_has_totp(request.user) and not verify_sensitive_action(request, request.user):
            return render(request, "accounts/totp_challenge.html", {"next": reverse_lazy("totp-disable")})
        TOTPDevice.objects.filter(user=request.user).delete()
        BackupCode.objects.filter(user=request.user).delete()
        messages.success(request, "2단계 인증이 비활성화되었습니다.")
        return redirect("account_email")
