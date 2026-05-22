from allauth.account.views import EmailView

from accounts.security import SensitiveActionMixin


class SensitiveEmailView(SensitiveActionMixin, EmailView):
    """Require TOTP when 2FA is enabled before changing account emails."""
