from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from accounts.security import SensitiveActionMixin
from accounts.totp_helpers import activate_totp_device, get_totp_setup_context


class AccountSettingsView(SensitiveActionMixin, LoginRequiredMixin, TemplateView):
    """Unified account management: email, password link, 2FA."""

    template_name = "account/settings.html"

    def get_context_data(self, **kwargs):
        from allauth.account.models import EmailAddress

        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        email_address = (
            EmailAddress.objects.filter(user=user, primary=True).first()
            or EmailAddress.objects.filter(user=user).order_by("pk").first()
        )
        ctx["email_address"] = email_address
        ctx["display_email"] = (email_address.email if email_address else user.email) or ""
        ctx.update(get_totp_setup_context(self.request))
        return ctx

    def post(self, request, *args, **kwargs):
        token = request.POST.get("token", "").strip()
        if token:
            if activate_totp_device(request, token):
                return redirect("account_settings")
            messages.error(request, "코드가 올바르지 않습니다.")
            return redirect("account_settings")
        return redirect("account_settings")
