from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import EmailTokenObtainPairView
from api.views import (
    CalendarEventsView,
    LessonCreateView,
    LessonViewSet,
    ProposalDismissView,
    StudentDetailView,
    StudentViewSet,
    SubjectViewSet,
    WeeklyReportView,
    WeeklyWeeksView,
)

router = DefaultRouter()
router.register("students", StudentViewSet, basename="student")
router.register("subjects", SubjectViewSet, basename="subject")

urlpatterns = [
    path("auth/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("calendar/events/", CalendarEventsView.as_view(), name="calendar-events"),
    path("lessons/", LessonCreateView.as_view(), name="lesson-create"),
    path("lessons/<int:pk>/", LessonViewSet.as_view({"patch": "partial_update"}), name="lesson-patch"),
    path("lessons/<int:pk>/complete/", LessonViewSet.as_view({"post": "complete"}), name="lesson-complete"),
    path("lessons/<int:pk>/cancel/", LessonViewSet.as_view({"post": "cancel"}), name="lesson-cancel"),
    path("proposals/dismiss/", ProposalDismissView.as_view(), name="proposal-dismiss"),
    path("reports/weekly/", WeeklyReportView.as_view(), name="weekly-report"),
    path("reports/weekly/weeks/", WeeklyWeeksView.as_view(), name="weekly-weeks"),
    path("students/<int:pk>/detail/", StudentDetailView.as_view(), name="student-detail"),
] + router.urls
