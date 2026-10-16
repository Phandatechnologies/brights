from django.urls import path

from .views import HealthCheckView, RequestInfoView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("staff/request-info/", RequestInfoView.as_view(), name="staff-request-info"),
]
