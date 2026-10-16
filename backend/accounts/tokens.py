"""
One-time links for email verification and password reset.

Both use Django's signed, time-limited tokens (valid for PASSWORD_RESET_TIMEOUT,
3 days by default). A token stops working as soon as it has been used, because
the values it was built from change:
  - verification tokens include email_verified_at (set when verified),
  - reset tokens include the password hash (changed when reset).
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import User


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "brights.accounts.EmailVerificationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.email}{user.email_verified_at}{timestamp}"


email_verification_token = EmailVerificationTokenGenerator()
password_reset_token = default_token_generator


def encode_uid(user) -> str:
    return urlsafe_base64_encode(force_bytes(user.pk))


def user_from_uid(uid: str):
    try:
        return User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
