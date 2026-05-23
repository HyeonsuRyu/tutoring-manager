from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import BackupCode
from accounts.security import user_has_totp, verify_sensitive_action


class TotpDisableView(LoginRequiredMixin, View):
    def post(self, request):
        if user_has_totp(request.user) and not verify_sensitive_action(request, request.user):
            return render(request, "accounts/totp_challenge.html", {"title": "2단계 인증"})
        TOTPDevice.objects.filter(user=request.user).delete()
        BackupCode.objects.filter(user=request.user).delete()
        messages.success(request, "2단계 인증이 비활성화되었습니다.")
        return redirect("account_settings")
