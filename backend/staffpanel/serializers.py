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
