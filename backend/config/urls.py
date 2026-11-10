from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path, re_path
from django.utils.http import url_has_allowed_host_and_scheme, urlencode

from core.spa import spa_index
from staffos import views as staffos_views



def admin_login(request):
    """
    The Django admin has no password-only login any more: staff sign in on the normal
    login page with password + emailed code, then come back here (same session).
    """
    target = request.GET.get("next") or f"/{settings.ADMIN_URL}"
    if not url_has_allowed_host_and_scheme(target, allowed_hosts=None) or not target.startswith("/"):
        target = f"/{settings.ADMIN_URL}"
    return HttpResponseRedirect(f"/login?{urlencode({'next': target})}")


urlpatterns = [
    path(f"{settings.ADMIN_URL}login/", admin_login, name="staff-admin-login"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/internal/staff-os/metrics/", staffos_views.metrics),
    path("api/", include("core.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("tutors.urls")),
    path("api/", include("profiles.urls")),
    path("api/", include("contact.urls")),
    path("api/", include("moderation.urls")),
    path("api/staff/", include("staffpanel.urls")),
    # Everything else is a page of the React app (e.g. /tutors/12, /dashboard).
    # Paths starting with api/, static/ or the admin are never sent to React.
    re_path(rf"^(?!api/|static/|{settings.ADMIN_URL})(?P<path>.*)$", spa_index, name="spa"),
]
