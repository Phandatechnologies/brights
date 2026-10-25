"""
One place that sends Brights' emails.

Sending can fail (mail server down, wrong key, a blocked network port). That must never
freeze or crash what the person was doing (signing up, reporting, an admin decision):
the failure is logged for us to fix, and the caller is told whether it worked.
EMAIL_TIMEOUT (settings) stops a slow mail server from holding a request open.
"""

import logging

from django.core.mail import send_mail

logger = logging.getLogger("brights.email")


def send_email(subject, body, from_email, recipient_list, **_ignored) -> bool:
    """Same arguments as Django's send_mail. Returns True if the email was handed to the mail server."""
    recipients = list(recipient_list)
    try:
        send_mail(subject, body, from_email, recipients)
        return True
    except Exception:
        # Subject and count only: email addresses are personal information and stay out of logs.
        logger.exception("Email failed: %r to %d recipient(s)", subject, len(recipients))
        return False
