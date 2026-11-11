from django.urls import path

from . import views

urlpatterns = [
    path("overview/", views.OverviewView.as_view(), name="staff-overview"),
    path("applications/", views.ApplicationListView.as_view(), name="staff-applications"),
    path("applications/<int:pk>/", views.ApplicationDetailView.as_view(), name="staff-application"),
    path("applications/<int:pk>/decide/", views.ApplicationDecisionView.as_view(), name="staff-application-decide"),
    path("photos/", views.PhotoListView.as_view(), name="staff-photos"),
    path("photos/<int:pk>/decide/", views.PhotoDecisionView.as_view(), name="staff-photo-decide"),
    path("reports/", views.ReportListView.as_view(), name="staff-reports"),
    path("reports/<int:pk>/", views.ReportDetailView.as_view(), name="staff-report"),
    path("reports/<int:pk>/decide/", views.ReportDecisionView.as_view(), name="staff-report-decide"),
    path("users/", views.UserListView.as_view(), name="staff-users"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="staff-user"),
    path("users/<int:pk>/action/", views.UserActionView.as_view(), name="staff-user-action"),
    path("videos/", views.VideoListView.as_view(), name="staff-videos"),
    path("videos/<int:pk>/", views.VideoDetailView.as_view(), name="staff-video"),
]
