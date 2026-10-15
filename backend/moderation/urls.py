from django.urls import path

from .views import ReportTutorView

urlpatterns = [
    path("tutors/<int:pk>/report/", ReportTutorView.as_view(), name="report-tutor"),
]
