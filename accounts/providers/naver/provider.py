from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class NaverAccount(ProviderAccount):
    def to_str(self):
        return self.account.extra_data.get("name") or self.account.extra_data.get("email", super().to_str())


class NaverProvider(OAuth2Provider):
    id = "naver"
    name = "Naver"
    account_class = NaverAccount

    def extract_uid(self, data):
        return str(data.get("response", {}).get("id", ""))

    def extract_common_fields(self, data):
        resp = data.get("response", {})
        return {
            "email": resp.get("email"),
            "name": resp.get("name") or resp.get("nickname"),
        }


provider_classes = [NaverProvider]
