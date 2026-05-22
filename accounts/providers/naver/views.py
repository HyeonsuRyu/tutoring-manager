from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter, OAuth2CallbackView, OAuth2LoginView

from accounts.providers.naver.provider import NaverProvider


class NaverOAuth2Adapter(OAuth2Adapter):
    provider_id = NaverProvider.id
    authorize_url = "https://nid.naver.com/oauth2.0/authorize"
    access_token_url = "https://nid.naver.com/oauth2.0/token"
    profile_url = "https://openapi.naver.com/v1/nid/me"


oauth2_login = OAuth2LoginView.adapter_view(NaverOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(NaverOAuth2Adapter)
