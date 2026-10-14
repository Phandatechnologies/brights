"""
The application review workflow ("state machine").

Every status change goes through a function in this file, which:
  1. locks the application row so two admins can't act on it at once,
  2. checks the change is allowed from the current status,
  3. checks who is allowed to make it,
  4. records an ApplicationEvent (the audit trail),
  5. emails the tutor once the database change has been saved.

Views and the admin call these functions; nothing else changes `status`.
"""

from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import ApplicationEvent, TutorApplication
from .notifications import notify_status_change
from .rules import (
    MIN_SUBJECT_MARK, REAPPLY_AFTER_DAYS, Pathway, Status, SubjectDecision, submission_errors,
)


def _lock(application_id):
    return TutorApplication.objects.select_for_update().get(pk=application_id)


def _record(application, actor, action, from_status, note="", details=None):
    ApplicationEvent.objects.create(
        application=application, actor=actor, action=action,
        from_status=from_status, to_status=application.status,
        note=note, details=details or [],
    )


def _require_reviewer(application, reviewer):
    if not (reviewer and reviewer.is_active and reviewer.is_staff):
        raise PermissionDenied("Only Brights administrators can review applications.")
    if reviewer.pk == application.user_id:
        raise PermissionDenied("You can't review your own application.")


def _require_status(application, *allowed):
    if application.status not in allowed:
        labels = ", ".join(dict(Status.CHOICES)[s] for s in allowed)
        raise ValidationError(
            f"This application is '{application.get_status_display()}'. This action needs: {labels}."
        )


def _require_note(note, what):
    if not (note or "").strip():
        raise ValidationError(f"Add a note explaining {what}. The tutor will see it.")
    return note.strip()


def _finish(application, actor, action, from_status, note="", details=None):
    application.save()
    _record(application, actor, action, from_status, note, details)
    transaction.on_commit(lambda: notify_status_change(application))
    return application


# --- Tutor actions -------------------------------------------------------------

@transaction.atomic
def submit(application_id, tutor):
    application = _lock(application_id)
    if application.user_id != tutor.pk:
        raise PermissionDenied("This isn't your application.")
    _require_status(application, Status.DRAFT, Status.MORE_INFO)

    errors = submission_errors(
        pathway=application.pathway,
        subjects=[(s.matric_mark, s.grades) for s in application.subjects.all()],
        document_kinds={d.kind for d in application.documents.all()},
        sace_number=application.sace_number,
        qualification_name=application.qualification_name,
    )
    if errors:
        raise ValidationError(errors)

    from_status = application.status
    application.status = Status.PENDING
    application.submitted_at = timezone.now()
    application.reviewer_message = ""
    application.subjects.update(decision=SubjectDecision.PENDING, decision_note="")  # fresh review
    application.save()
    _record(application, tutor, "submitted", from_status)
    return application


def reapply_available_from(application):
    """Date from which a rejected tutor may start again, or None if not rejected."""
    if application.status != Status.REJECTED or not application.reviewed_at:
        return None
    return application.reviewed_at + timedelta(days=REAPPLY_AFTER_DAYS)


@transaction.atomic
def reapply(application_id, tutor):
    application = _lock(application_id)
    if application.user_id != tutor.pk:
        raise PermissionDenied("This isn't your application.")
    _require_status(application, Status.REJECTED)
    available = reapply_available_from(application)
    if available and timezone.now() < available:
        raise ValidationError(f"You can apply again from {timezone.localtime(available):%d %B %Y}.")

    from_status = application.status
    application.status = Status.DRAFT
    application.reviewer_message = ""
    application.submitted_at = None
    application.subjects.update(decision=SubjectDecision.PENDING, decision_note="")
    application.save()
    _record(application, tutor, "reapplied", from_status)
    return application


# --- Reviewer actions ------------------------------------------------------------

@transaction.atomic
def approve(application_id, reviewer, decisions, message=""):
    """
    decisions: {application_subject_id: ("approved" | "declined", note)}
    Every subject needs a decision; declined subjects need a note;
    at least one subject must be approved.
    """
    application = _lock(application_id)
    _require_reviewer(application, reviewer)
    _require_status(application, Status.PENDING)

    subjects = list(application.subjects.select_related("subject"))
    problems = []
    for item in subjects:
        decision, note = decisions.get(item.pk, (SubjectDecision.PENDING, ""))
        note = (note or "").strip()
        if decision not in (SubjectDecision.APPROVED, SubjectDecision.DECLINED):
            problems.append(f"{item.subject.name}: choose approve or decline.")
        elif decision == SubjectDecision.DECLINED and not note:
            problems.append(f"{item.subject.name}: add a reason for declining.")
        elif (decision == SubjectDecision.APPROVED and application.pathway == Pathway.ACADEMIC
              and (item.matric_mark or 0) < MIN_SUBJECT_MARK):
            problems.append(f"{item.subject.name}: can't be approved below {MIN_SUBJECT_MARK}%.")
        item.decision, item.decision_note = decision, note
    if problems:
        raise ValidationError(problems)
    if not any(i.decision == SubjectDecision.APPROVED for i in subjects):
        raise ValidationError("Approve at least one subject, or reject the application instead.")

    for item in subjects:
        item.save(update_fields=["decision", "decision_note"])

    from_status = application.status
    application.status = Status.APPROVED
    application.reviewer_message = (message or "").strip()
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer
    details = [{"subject": i.subject.name, "decision": i.decision, "note": i.decision_note} for i in subjects]
    return _finish(application, reviewer, "approved", from_status, application.reviewer_message, details)


@transaction.atomic
def request_more_info(application_id, reviewer, message):
    application = _lock(application_id)
    _require_reviewer(application, reviewer)
    _require_status(application, Status.PENDING)
    message = _require_note(message, "what information is needed")
    from_status = application.status
    application.status = Status.MORE_INFO
    application.reviewer_message = message
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer
    return _finish(application, reviewer, "requested_info", from_status, message)


@transaction.atomic
def reject(application_id, reviewer, message):
    application = _lock(application_id)
    _require_reviewer(application, reviewer)
    _require_status(application, Status.PENDING)
    message = _require_note(message, "why the application was rejected")
    from_status = application.status
    application.status = Status.REJECTED
    application.reviewer_message = message
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer
    return _finish(application, reviewer, "rejected", from_status, message)


@transaction.atomic
def suspend(application_id, reviewer, message):
    application = _lock(application_id)
    _require_reviewer(application, reviewer)
    _require_status(application, Status.APPROVED)
    message = _require_note(message, "why the tutor is suspended")
    from_status = application.status
    application.status = Status.SUSPENDED
    application.reviewer_message = message
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer
    return _finish(application, reviewer, "suspended", from_status, message)


@transaction.atomic
def reinstate(application_id, reviewer, message=""):
    application = _lock(application_id)
    _require_reviewer(application, reviewer)
    _require_status(application, Status.SUSPENDED)
    from_status = application.status
    application.status = Status.APPROVED
    application.reviewer_message = (message or "").strip()
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer
    return _finish(application, reviewer, "reinstated", from_status, application.reviewer_message)
