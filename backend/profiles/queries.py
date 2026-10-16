"""
Who appears in search. This is the single source of truth for discoverability:
both the search results and individual profile pages use it.
"""

from django.db.models import Exists, OuterRef, Q

from tutors.models import ApplicationSubject
from tutors.rules import Status, SubjectDecision

from .models import TutorProfile


def approved_subjects():
    return ApplicationSubject.objects.filter(decision=SubjectDecision.APPROVED)


def discoverable_profiles():
    """
    A tutor is shown only if ALL of these are true:
      - their account is active (not deactivated),
      - their application is approved (so not pending, rejected or suspended),
      - they have at least one approved subject,
      - their profile is complete,
      - no open child-safety report from someone who contacted them is waiting for review.
    """
    from moderation.models import Report
    from moderation.rules import ReportStatus

    has_approved_subject = approved_subjects().filter(application__user=OuterRef("user"))
    on_safety_hold = Report.objects.filter(tutor=OuterRef("pk"), holds_tutor=True, status=ReportStatus.OPEN)
    return (
        TutorProfile.objects
        .select_related("user", "area", "user__tutor_application")
        .filter(
            user__is_active=True,
            user__tutor_application__status=Status.APPROVED,
            hourly_rate__isnull=False,
        )
        .exclude(bio="")
        .exclude(whatsapp_number="")
        .filter(Q(teaches_online=True) | Q(teaches_in_person=True))
        .exclude(Q(teaches_in_person=True) & Q(area__isnull=True))
        .filter(Exists(has_approved_subject))
        .exclude(Exists(on_safety_hold))
    )


def search(params):
    """
    Filters (all optional):
      subject, grade, mode (online | in_person), province, area, min_price, max_price, sort.

    Location: in-person tutors are matched by area/province. Online tutors are
    discoverable nationally, so they match any location unless mode=in_person.
    """
    qs = discoverable_profiles()

    subject = _int(params.get("subject"))
    grade = _int(params.get("grade"))
    if subject or grade:
        match = approved_subjects().filter(application__user=OuterRef("user"))
        if subject:
            match = match.filter(subject_id=subject)
        if grade:
            match = match.filter(grades__contains=[grade])
        qs = qs.filter(Exists(match))

    mode = params.get("mode")
    area = _int(params.get("area"))
    province = params.get("province")
    location = Q()
    if area:
        location &= Q(area_id=area)
    if province:
        location &= Q(area__province=province)

    if mode == "online":
        qs = qs.filter(teaches_online=True)
    elif mode == "in_person":
        qs = qs.filter(Q(teaches_in_person=True) & location)
    elif area or province:
        qs = qs.filter((Q(teaches_in_person=True) & location) | Q(teaches_online=True))

    min_price = _int(params.get("min_price"))
    max_price = _int(params.get("max_price"))
    if min_price is not None:
        qs = qs.filter(hourly_rate__gte=min_price)
    if max_price is not None:
        qs = qs.filter(hourly_rate__lte=max_price)

    ordering = {
        "price_low": ["hourly_rate", "id"],
        "price_high": ["-hourly_rate", "id"],
    }.get(params.get("sort"), ["-user__tutor_application__reviewed_at", "id"])  # newest approved first
    return qs.order_by(*ordering)


def _int(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
