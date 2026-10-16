from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from core.spa import spa_index

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/", include("core.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("tutors.urls")),
    path("api/", include("profiles.urls")),
    path("api/", include("contact.urls")),
    path("api/", include("moderation.urls")),
    # Everything else is a page of the React app (e.g. /tutors/12, /dashboard).
    # Paths starting with api/, static/ or the admin are never sent to React.
    re_path(rf"^(?!api/|static/|{settings.ADMIN_URL})(?P<path>.*)$", spa_index, name="spa"),
]
