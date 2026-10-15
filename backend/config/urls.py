from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("tutors.urls")),
    path("api/", include("profiles.urls")),
    path("api/", include("contact.urls")),
    path("api/", include("moderation.urls")),
]
