"""Serves the built React app (frontend/dist/index.html) for every non-API page."""

from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_safe



@require_safe
def spa_index(request, path=""):
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise Http404("The frontend has not been built (run npm run build in frontend/).")
    response = HttpResponse(index.read_bytes(), content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = settings.CONTENT_SECURITY_POLICY
    response["Cache-Control"] = "no-cache"  # always fetch the latest index.html; assets are cache-busted
    response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    return response

