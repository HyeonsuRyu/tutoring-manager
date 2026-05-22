from django.urls import path

from accounts.providers.naver import views

urlpatterns = [
    path("login/", views.oauth2_login, name="naver_login"),
    path("login/callback/", views.oauth2_callback, name="naver_callback"),
]
