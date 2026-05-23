from django.urls import path

from students import views
from students import views_progress_import

urlpatterns = [
    path("settings/subjects/", views.SubjectListView.as_view(), name="subject-list"),
    path("settings/subjects/<int:pk>/delete/", views.SubjectDeleteView.as_view(), name="subject-delete"),
    path("timezone-suggest.json", views.TimezoneSuggestView.as_view(), name="timezone-suggest"),
    path("progress/", views.ProgressHubView.as_view(), name="progress-hub"),
    path("progress/import/", views_progress_import.ProgressImportUploadView.as_view(), name="progress-import"),
    path(
        "progress/import/review/",
        views_progress_import.ProgressImportReviewView.as_view(),
        name="progress-import-review",
    ),
    path(
        "progress/import/apply/",
        views_progress_import.ProgressImportApplyView.as_view(),
        name="progress-import-apply",
    ),
    path(
        "progress/import/template/",
        views_progress_import.ProgressImportTemplateDownloadView.as_view(),
        name="progress-import-template",
    ),
    path("progress/<int:pk>/", views.ProgressChartView.as_view(), name="student-progress"),
    path("", views.StudentListView.as_view(), name="student-list"),
    path("new/", views.StudentCreateView.as_view(), name="student-create"),
    path("<int:pk>/", views.StudentDetailView.as_view(), name="student-detail"),
    path("<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student-update"),
]
