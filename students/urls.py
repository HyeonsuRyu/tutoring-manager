from django.urls import path

from students import views

urlpatterns = [
    path("settings/subjects/", views.SubjectListView.as_view(), name="subject-list"),
    path("settings/subjects/<int:pk>/delete/", views.SubjectDeleteView.as_view(), name="subject-delete"),
    path("timezone-suggest.json", views.TimezoneSuggestView.as_view(), name="timezone-suggest"),
    path("", views.StudentListView.as_view(), name="student-list"),
    path("new/", views.StudentCreateView.as_view(), name="student-create"),
    path("<int:pk>/", views.StudentDetailView.as_view(), name="student-detail"),
    path("<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student-update"),
    path("<int:pk>/progress/", views.ProgressChartView.as_view(), name="student-progress"),
]
