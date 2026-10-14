from django.urls import path

from . import views

urlpatterns = [
    path("subjects/", views.SubjectListView.as_view(), name="subject-list"),
    path("tutor/application/", views.MyApplicationView.as_view(), name="my-application"),
    path("tutor/application/submit/", views.SubmitApplicationView.as_view(), name="application-submit"),
    path("tutor/application/reapply/", views.ReapplyView.as_view(), name="application-reapply"),
    path("tutor/application/documents/", views.DocumentUploadView.as_view(), name="document-upload"),
    path("tutor/application/documents/<int:pk>/", views.DocumentDeleteView.as_view(), name="document-delete"),
    path("staff/documents/<int:pk>/download/", views.StaffDocumentDownloadView.as_view(), name="staff-document-download"),
]
