"""Report emails. Kept short; no details of what was reported or what action was taken."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse


def admin_recipients():
    configured = getattr(settings, "REPORT_ALERT_EMAILS", [])
    if configured:
        return configured
    User = get_user_model()
    return list(User.objects.filter(is_superuser=True, is_active=True).values_list("email", flat=True))


def notify_admins_urgent(report):
    recipients = admin_recipients()
    if not recipients:
        return
    link = settings.BACKEND_URL.rstrip("/") + reverse("admin:moderation_report_review", args=[report.pk])
    send_mail(
        f"URGENT: child-safety report #{report.pk}",
        "A child-safety report was submitted. "
        + ("The tutor has been hidden from search until it is reviewed.\n\n" if report.holds_tutor
           else "The reporter has not contacted this tutor through Brights, so the tutor is still visible. "
                "Review it urgently.\n\n")
        +
        f"Review it now:\n{link}\n",
        None, recipients,
    )


def notify_reporter_received(report):
    if report.reporter:
        send_mail(
            "We received your report",
            f"Hi {report.reporter.first_name},\n\nThank you for telling us. Our team will review your report "
            "and take action if needed. For your privacy and the tutor's, we won't share the details of what "
            "action is taken, but we'll let you know when the review is finished.\n\n"
            "If a child is in immediate danger, contact SAPS on 10111 or Childline on 116.\n\nThe Brights team",
            None, [report.reporter.email],
        )


def notify_reporter_closed(report):
    if report.reporter:
        send_mail(
            "We've reviewed your report",
            f"Hi {report.reporter.first_name},\n\nOur team has finished reviewing your report. Thank you for "
            "helping keep Brights safe.\n\nThe Brights team",
            None, [report.reporter.email],
        )


def notify_tutor_warning(report, message):
    user = report.tutor.user
    send_mail(
        "A warning about your Brights tutor account",
        f"Hi {user.first_name},\n\nOur team has reviewed a concern about your conduct on Brights.\n\n{message}\n\n"
        "Further concerns may lead to your account being suspended.\n\nThe Brights team",
        None, [user.email],
    )
