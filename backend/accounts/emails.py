"""Account emails. Links point to the React frontend, which calls the API."""

from django.conf import settings
from core.mail import send_email

from .tokens import email_verification_token, encode_uid, password_reset_token


def _link(path, user, token):
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}?uid={encode_uid(user)}&token={token}"


def send_verification_email(user) -> bool:
    link = _link("/verify-email", user, email_verification_token.make_token(user))
    return send_email(
        "Confirm your email for Brights",
        f"Hi {user.first_name},\n\nPlease confirm your email address by opening this link:\n{link}\n\n"
        "The link works for 3 days. If you didn't create a Brights account, you can ignore this email.\n\nThe Brights team",
        None, [user.email],
    )


def send_password_reset_email(user) -> bool:
    link = _link("/reset-password", user, password_reset_token.make_token(user))
    return send_email(
        "Reset your Brights password",
        f"Hi {user.first_name},\n\nSomeone asked to reset the password for your Brights account. "
        f"If it was you, open this link to choose a new password:\n{link}\n\n"
        "The link works for 3 days and can only be used once. If you didn't ask for this, ignore this email; "
        "your password won't change.\n\nThe Brights team",
        None, [user.email],
    )


def send_staff_login_code(user, code) -> bool:
    return send_email(
        f"Your Brights sign-in code: {code}",
        f"Hi {user.first_name},\n\nYour code to finish signing in to Brights is:\n\n    {code}\n\n"
        "It works once, for 10 minutes. Never share it: the Brights team will never ask you for it.\n\n"
        "If you didn't just try to sign in, someone may know your password. Change it straight away "
        "with \"Forgot your password?\" on the login page.\n\nThe Brights team",
        None, [user.email],
    )
