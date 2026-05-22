from allauth.account.views import PasswordChangeView

from accounts.security import SensitiveActionMixin


class SensitivePasswordChangeView(SensitiveActionMixin, PasswordChangeView):
    """Require TOTP when 2FA is enabled before changing password."""
