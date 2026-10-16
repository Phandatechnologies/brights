"""
Login with a per-account lockout: after 10 failed attempts for one email within
15 minutes, that account can't log in for 15 minutes, whatever IP the attempts come
from. Applies to the API login and the admin login (both use authenticate()).
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.dispatch import receiver

MAX_FAILURES = 10
LOCK_SECONDS = 15 * 60


def _key(username):
    return f"login-failures:{(username or '').strip().lower()}"


def is_locked(username) -> bool:
    return cache.get(_key(username), 0) >= MAX_FAILURES


class LockoutModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        username = username or kwargs.get("email")
        if username and is_locked(username):
            return None
        return super().authenticate(request, username=username, password=password, **kwargs)


@receiver(user_login_failed)
def count_failure(sender, credentials, **kwargs):
    username = credentials.get("username") or credentials.get("email")
    if not username:
        return
    key = _key(username)
    cache.add(key, 0, LOCK_SECONDS)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, LOCK_SECONDS)


@receiver(user_logged_in)
def reset_failures(sender, user, **kwargs):
    cache.delete(_key(user.email))
