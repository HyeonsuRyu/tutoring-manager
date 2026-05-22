from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("api/v1/", include("api.urls")),
    path("students/", include("students.urls")),
    path("reports/", include("reports.urls")),
    path("", include("calendar_app.urls")),
]
