from django.urls import path

from reports.views import WeeklyReportView

urlpatterns = [
    path("weekly/", WeeklyReportView.as_view(), name="weekly-report"),
]
