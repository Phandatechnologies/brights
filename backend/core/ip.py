"""Find the visitor's real IP address without trusting values an attacker can fake."""

from django.conf import settings


def client_ip(request) -> str:
    """
    Behind N trusted proxies, the real client is the Nth address from the right
    in X-Forwarded-For (proxies append; anything further left could be forged).
    With no trusted proxies we use the direct connection address.
    """
    remote = request.META.get("REMOTE_ADDR", "")
    proxies = settings.TRUSTED_PROXY_COUNT
    if proxies <= 0:
        return remote
    forwarded = [part.strip() for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if part.strip()]
    if len(forwarded) >= proxies:
        return forwarded[-proxies]
    return remote
