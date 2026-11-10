"""
Two-step login for Brights staff (they can open tutors' ID documents, so a password alone isn't enough).

1. The normal login checks the password. For staff it doesn't log in yet: it emails a 6-digit code.
2. The staff member types the code; only then is the session created.

Codes: random, stored only as a keyed hash, single use, expire after 10 minutes, 5 tries each.
Asking for a new code cancels the old one.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import StaffLoginCode

CODE_LIFETIME = timedelta(minutes=10)
MAX_TRIES = 5


def _hash(challenge: str, code: str) -> str:
    key = settings.SECRET_KEY.encode()
    return hmac.new(key, f"staff-login:{challenge}:{code}".encode(), hashlib.sha256).hexdigest()


def start(user) -> tuple[str, str]:
    """Create a fresh code for this staff member. Returns (challenge, code)."""
    StaffLoginCode.objects.filter(user=user).delete()  # only the newest code works
    StaffLoginCode.objects.filter(expires_at__lt=timezone.now()).delete()  # tidy up old ones
    challenge = secrets.token_urlsafe(32)
    code = f"{secrets.randbelow(1_000_000):06d}"
    StaffLoginCode.objects.create(user=user, challenge=challenge, code_hash=_hash(challenge, code),
                                  expires_at=timezone.now() + CODE_LIFETIME)
    return challenge, code


class CodeError(Exception):
    pass


def check(challenge: str, code: str):
    """Return the user if the code is right. Raises CodeError with a message to show otherwise."""
    # The database work finishes (and is saved) before any error is raised. Raising inside the
    # transaction would undo the "one more try used" update and allow unlimited guesses.
    user, problem = _check(challenge, code)
    if problem:
        raise CodeError(problem)
    return user


@transaction.atomic
def _check(challenge, code):
    entry = (StaffLoginCode.objects.select_for_update().select_related("user")
             .filter(challenge=str(challenge or "")[:64]).first())
    if entry is None or entry.expires_at < timezone.now():
        if entry:
            entry.delete()
        return None, "This code has expired. Log in again to get a new one."
    if entry.attempts >= MAX_TRIES:
        entry.delete()
        return None, "Too many wrong codes. Log in again to get a new one."
    code = "".join(ch for ch in str(code or "") if ch.isdigit())
    if not hmac.compare_digest(entry.code_hash, _hash(entry.challenge, code)):
        entry.attempts += 1
        left = MAX_TRIES - entry.attempts
        if left <= 0:
            entry.delete()
            return None, "Too many wrong codes. Log in again to get a new one."
        entry.save(update_fields=["attempts"])
        return None, f"That code isn't right. {left} {'try' if left == 1 else 'tries'} left."
    user = entry.user
    entry.delete()  # single use
    if not (user.is_active and user.is_staff):
        return None, "This account can't sign in."
    return user, None
