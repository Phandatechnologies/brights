"""
Emails to tutors about their application. Deliberately short and free of
sensitive detail (no marks, no ID information): the dashboard has the specifics.
In development, EMAIL_BACKEND prints emails in the runserver terminal.
"""

from django.conf import settings
from core.mail import send_email

from .rules import Status

SUBJECTS = {
    Status.APPROVED: "You're approved to tutor on Brights",
    Status.MORE_INFO: "Brights needs more information for your tutor application",
    Status.REJECTED: "Update on your Brights tutor application",
    Status.SUSPENDED: "Your Brights tutor account has been suspended",
}

BODIES = {
    Status.APPROVED: "Good news: your tutor application has been approved.",
    Status.MORE_INFO: "Our review team needs a bit more information before they can decide on your application.",
    Status.REJECTED: "We weren't able to approve your tutor application this time.",
    Status.SUSPENDED: "Your tutor account has been suspended, so you won't appear in search for now.",
}


def notify_status_change(application):
    status = application.status
    if status not in SUBJECTS:
        return
    user = application.user
    link = f"{settings.FRONTEND_URL.rstrip('/')}/tutor/apply"
    body = (
        f"Hi {user.first_name},\n\n"
        f"{BODIES[status]}\n\n"
        f"Log in to see the details and any note from our team:\n{link}\n\n"
        "The Brights team"
    )
    send_email(SUBJECTS[status], body, None, [user.email])
