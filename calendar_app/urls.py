from django.urls import path

from calendar_app import views

urlpatterns = [
    path("", views.HomeCalendarView.as_view(), name="home"),
    path("events.json", views.CalendarEventsJsonView.as_view(), name="calendar-events-json"),
    path("lessons/<int:pk>/complete/", views.LessonCompleteView.as_view(), name="lesson-complete-web"),
    path("lessons/approve/", views.LessonApproveView.as_view(), name="lesson-approve-web"),
    path("lessons/create/", views.LessonManualCreateView.as_view(), name="lesson-create-web"),
    path("proposals/dismiss/", views.LessonDismissView.as_view(), name="proposal-dismiss-web"),
    path("lessons/<int:pk>/cancel/", views.LessonCancelView.as_view(), name="lesson-cancel-web"),
]
