"""Plain dictionaries for the staff API (kept simple and explicit: staff see exactly these fields)."""

from django.urls import reverse
from django.utils import timezone

from tutors.rules import MIN_SUBJECT_MARK, Pathway, Status


def _name(user):
    return f"{user.first_name} {user.last_name}".strip()


def application_row(application):
    user = application.user
    waiting = (timezone.now() - application.submitted_at).days if application.submitted_at else None
    return {
        "id": application.pk,
        "name": _name(user),
        "email": user.email,
        "pathway": application.pathway,
        "pathway_label": application.get_pathway_display(),
        "status": application.status,
        "status_label": application.get_status_display(),
        "subject_count": getattr(application, "subject_count", None),
        "submitted_at": application.submitted_at,
        "updated_at": application.updated_at,
        "days_waiting": waiting if application.status == Status.PENDING else None,
    }


def application_detail(application, viewer):
    user = application.user
    can_view_documents = viewer.has_perm("tutors.view_applicationdocument")
    is_own = application.user_id == viewer.pk
    subjects = [{
        "id": item.pk,
        "subject": item.subject.name,
        "matric_mark": item.matric_mark,
        "grades": item.grades,
        "decision": item.decision,
        "decision_note": item.decision_note,
        "below_minimum": application.pathway == Pathway.ACADEMIC and (item.matric_mark or 0) < MIN_SUBJECT_MARK,
    } for item in application.subjects.select_related("subject")]
    documents = [{
        "id": doc.pk,
        "kind": doc.kind,
        "kind_label": doc.get_kind_display(),
        "name": doc.original_name,
        "content_type": doc.content_type,
        "size": doc.size,
        "uploaded_at": doc.uploaded_at,
        "url": reverse("staff-document-download", args=[doc.pk]) if can_view_documents else None,
    } for doc in application.documents.all()]
    history = [{
        "action": event.action,
        "actor": event.actor.email if event.actor else None,
        "from_status": event.from_status,
        "to_status": event.to_status,
        "note": event.note,
        "details": event.details,
        "created_at": event.created_at,
    } for event in application.events.select_related("actor").order_by("-created_at")]
    profile = getattr(user, "tutor_profile", None)
    actions = []
    if not is_own:
        if application.status == Status.PENDING:
            actions = ["approve", "request_info", "reject"]
        elif application.status == Status.APPROVED:
            actions = ["suspend"]
        elif application.status == Status.SUSPENDED:
            actions = ["reinstate"]
    return {
        **application_row(application),
        "first_name": user.first_name,
        "date_of_birth": user.date_of_birth,
        "age": user.age,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
        "sace_number": application.sace_number,
        "qualification_name": application.qualification_name,
        "reviewer_message": application.reviewer_message,
        "reviewed_at": application.reviewed_at,
        "reviewed_by": application.reviewed_by.email if application.reviewed_by else None,
        "min_mark": MIN_SUBJECT_MARK,
        "subjects": subjects,
        "documents": documents,
        "can_view_documents": can_view_documents,
        "history": history,
        "is_own": is_own,
        "actions": actions,
        "profile_id": profile.pk if profile else None,
    }


# ---- Photos ---------------------------------------------------------------------------------

def photo_row(profile):
    from profiles.photo_review import photo_version

    user = profile.user
    version = photo_version(profile)
    return {
        "id": profile.pk,
        "name": _name(user),
        "email": user.email,
        "photo_status": profile.photo_status,
        "photo_note": profile.photo_note,
        "version": version,
        "photo_url": f"{reverse('staff-tutor-photo', args=[profile.pk])}?v={version}" if version else None,
        "updated_at": profile.updated_at,
    }


# ---- Reports --------------------------------------------------------------------------------

def report_row(report):
    reporter = report.reporter
    return {
        "id": report.pk,
        "category": report.category,
        "category_label": report.get_category_display(),
        "is_urgent": report.is_urgent,
        "holds_tutor": report.holds_tutor,
        "status": report.status,
        "outcome": report.outcome,
        "outcome_label": report.get_outcome_display() if report.outcome else "",
        "tutor_name": report.tutor.full_name,
        "reporter_name": _name(reporter) if reporter else "Deleted account",
        "created_at": report.created_at,
        "closed_at": report.closed_at,
        "days_open": (timezone.now() - report.created_at).days if report.status == "open" else None,
    }


def report_detail(report, viewer):
    from contact.models import ContactEvent
    from moderation.models import Report

    tutor_user = report.tutor.user
    reporter = report.reporter
    application = getattr(tutor_user, "tutor_application", None)
    contacts = (ContactEvent.objects.filter(requester=reporter, tutor=report.tutor).select_related("subject").order_by("-created_at")
                if reporter else [])
    others = Report.objects.filter(tutor=report.tutor).exclude(pk=report.pk).select_related("tutor__user", "reporter").order_by("-created_at")
    is_own = tutor_user.pk == viewer.pk
    return {
        **report_row(report),
        "description": report.description,
        "incident_date": report.incident_date,
        "reporter_was_minor": report.reporter_was_minor,
        "reporter": {
            "name": _name(reporter), "email": reporter.email, "account_type": reporter.get_account_type_display(),
        } if reporter else None,
        "tutor": {
            "name": report.tutor.full_name,
            "email": tutor_user.email,
            "profile_id": report.tutor.pk,
            "application_id": application.pk if application else None,
            "application_status": application.status if application else None,
            "application_status_label": application.get_status_display() if application else None,
            "accepting_learners": report.tutor.accepting_learners,
        },
        "contacts": [{"subject": c.subject.name, "grade": c.grade, "created_at": c.created_at} for c in contacts],
        "other_reports": [report_row(r) for r in others],
        "admin_notes": report.admin_notes,
        "closed_by": report.closed_by.email if report.closed_by else None,
        "is_own": is_own,
        "actions": ["dismiss", "warn", "suspend"] if report.status == "open" and not is_own else [],
    }
