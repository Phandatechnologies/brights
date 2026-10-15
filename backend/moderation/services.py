"""
Report workflow. Closing a report is the only way it leaves the queue, and each
closing action records who did it and why. Suspension reuses the tutor review
workflow (tutors.services.suspend) so it lands in the application's audit trail too.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from tutors import services as tutor_services
from tutors.rules import Status

from . import notifications
from .models import Report
from .rules import Outcome, ReportStatus


def _lock_open(report_id, admin):
    report = Report.objects.select_for_update().select_related("tutor__user").get(pk=report_id)
    if not (admin and admin.is_active and admin.is_staff):
        raise PermissionDenied("Only Brights administrators can handle reports.")
    if report.tutor.user_id == admin.pk:
        raise PermissionDenied("You can't handle a report about yourself.")
    if report.status != ReportStatus.OPEN:
        raise ValidationError("This report is already closed.")
    return report


def _close(report, admin, outcome, notes):
    report.status = ReportStatus.CLOSED
    report.outcome = outcome
    report.closed_at = timezone.now()
    report.closed_by = admin
    if notes:
        stamp = timezone.localtime().strftime("%Y-%m-%d %H:%M")
        report.admin_notes = (report.admin_notes + f"\n[{stamp} {admin.email}] {notes}").strip()
    report.save()
    transaction.on_commit(lambda: notifications.notify_reporter_closed(report))
    return report


@transaction.atomic
def dismiss(report_id, admin, notes):
    report = _lock_open(report_id, admin)
    if not (notes or "").strip():
        raise ValidationError("Add an internal note explaining why the report is dismissed.")
    return _close(report, admin, Outcome.DISMISSED, notes.strip())


@transaction.atomic
def warn(report_id, admin, message_to_tutor, notes=""):
    report = _lock_open(report_id, admin)
    message_to_tutor = (message_to_tutor or "").strip()
    if not message_to_tutor:
        raise ValidationError("Write the warning the tutor will receive.")
    _close(report, admin, Outcome.WARNED, (notes or "").strip() or f"Warning sent: {message_to_tutor}")
    transaction.on_commit(lambda: notifications.notify_tutor_warning(report, message_to_tutor))
    return report


@transaction.atomic
def suspend(report_id, admin, message_to_tutor, notes=""):
    report = _lock_open(report_id, admin)
    message_to_tutor = (message_to_tutor or "").strip()
    if not message_to_tutor:
        raise ValidationError("Write the reason the tutor will see for the suspension.")
    application = report.tutor.user.tutor_application
    if application.status == Status.APPROVED:
        tutor_services.suspend(application.pk, admin, message_to_tutor)
    elif application.status != Status.SUSPENDED:
        raise ValidationError(f"The tutor's application is '{application.get_status_display()}', so it can't be suspended.")
    return _close(report, admin, Outcome.SUSPENDED, (notes or "").strip() or f"Suspended: {message_to_tutor}")
