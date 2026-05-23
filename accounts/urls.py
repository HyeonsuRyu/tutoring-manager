from django.urls import include, path, re_path
from django.views.generic import RedirectView

from allauth.account.views import confirm_email

from accounts import views_2fa
from accounts.views_account import AccountSettingsView
from accounts.views_password import SensitivePasswordChangeView

urlpatterns = [
    # allauth ko locale attaches "을" after trailing-slash URLs → .../key/을 (404). Allow junk segment.
    re_path(
        r"^confirm-email/(?P<key>[-:\w]+)(?:/[^/]+)?/?$",
        confirm_email,
        name="account_confirm_email",
    ),
    path("settings/", AccountSettingsView.as_view(), name="account_settings"),
    path(
        "email/",
        RedirectView.as_view(pattern_name="account_settings", permanent=False),
        name="account_email",
    ),
    path("password/change/", SensitivePasswordChangeView.as_view(), name="account_change_password"),
    path(
        "2fa/setup/",
        RedirectView.as_view(pattern_name="account_settings", permanent=False),
        name="totp-setup",
    ),
    path("2fa/disable/", views_2fa.TotpDisableView.as_view(), name="totp-disable"),
    path("naver/", include("accounts.providers.naver.urls")),
]
