from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

from .ip import client_ip

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 15 * 60


class AdminLoginRateLimitMiddleware:
    """
    Slows down password guessing on the Django admin login page:
    at most 10 login attempts per IP address per 15 minutes.
    (The API login has its own limit through Django REST Framework.)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.login_path = f"/{settings.ADMIN_URL}login/"

    def __call__(self, request):
        if request.method == "POST" and request.path == self.login_path:
            key = f"admin-login:{client_ip(request)}"
            cache.add(key, 0, WINDOW_SECONDS)
            try:
                attempts = cache.incr(key)
            except ValueError:  # expired between add and incr
                cache.set(key, 1, WINDOW_SECONDS)
                attempts = 1
            if attempts > MAX_ATTEMPTS:
                return HttpResponse(
                    "Too many login attempts. Please wait 15 minutes and try again.",
                    status=429, content_type="text/plain",
                )
        return self.get_response(request)


MAX_REQUEST_BYTES = 8 * 1024 * 1024  # largest upload is 5 MB; leave room for form overhead


class RequestSizeLimitMiddleware:
    """Refuse request bodies over 8 MB before they are read, so uploads can't fill the disk."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length > MAX_REQUEST_BYTES:
            return HttpResponse("Request too large.", status=413, content_type="text/plain")
        return self.get_response(request)
