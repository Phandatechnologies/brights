from django.urls import path

from . import views

urlpatterns = [
    path("tutors/<int:pk>/contact/", views.ContactTutorView.as_view(), name="contact-tutor"),
    path("contact/safety/", views.SafetyAcknowledgementView.as_view(), name="contact-safety"),
    path("contact/history/", views.ContactHistoryView.as_view(), name="contact-history"),
]
