"""Account emails. Links point to the React frontend, which calls the API."""

from django.conf import settings
from django.core.mail import send_mail

from .tokens import email_verification_token, encode_uid, password_reset_token


def _link(path, user, token):
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}?uid={encode_uid(user)}&token={token}"


def send_verification_email(user):
    link = _link("/verify-email", user, email_verification_token.make_token(user))
    send_mail(
        "Confirm your email for Brights",
        f"Hi {user.first_name},\n\nPlease confirm your email address by opening this link:\n{link}\n\n"
        "The link works for 3 days. If you didn't create a Brights account, you can ignore this email.\n\nThe Brights team",
        None, [user.email],
    )


def send_password_reset_email(user):
    link = _link("/reset-password", user, password_reset_token.make_token(user))
    send_mail(
        "Reset your Brights password",
        f"Hi {user.first_name},\n\nSomeone asked to reset the password for your Brights account. "
        f"If it was you, open this link to choose a new password:\n{link}\n\n"
        "The link works for 3 days and can only be used once. If you didn't ask for this, ignore this email; "
        "your password won't change.\n\nThe Brights team",
        None, [user.email],
    )
