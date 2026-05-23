from django.views.generic import TemplateView

from accounts.security import SensitiveActionMixin


class SensitiveEmailView(SensitiveActionMixin, TemplateView):
    """Show the single account email (read-only). Email management actions are disabled."""

    template_name = "account/email.html"

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
        return ctx

    def post(self, request, *args, **kwargs):
        """Email add/remove/primary/resend are not offered on this page."""
        from django.shortcuts import redirect

        return redirect("account_email")
