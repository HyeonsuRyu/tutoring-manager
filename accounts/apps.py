from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from allauth.socialaccount.providers import registry

        from accounts.providers.naver.provider import NaverProvider

        registry.register(NaverProvider)
