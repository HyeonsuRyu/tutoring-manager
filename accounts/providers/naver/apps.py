from django.apps import AppConfig


class NaverProviderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts.providers.naver"
    label = "naver_provider"
