from django.urls import path

from . import views

urlpatterns = [
    path("overview/", views.OverviewView.as_view(), name="staff-overview"),
    path("applications/", views.ApplicationListView.as_view(), name="staff-applications"),
    path("applications/<int:pk>/", views.ApplicationDetailView.as_view(), name="staff-application"),
    path("applications/<int:pk>/decide/", views.ApplicationDecisionView.as_view(), name="staff-application-decide"),
]
