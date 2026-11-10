"""Brights' weekly totals for Phanda Staff OS.

Brights has learners aged 12 to 17, so the rule here is stricter than anywhere else:
- whole-platform totals per week only: never broken down by age, grade, area, school or subject;
- nothing about any person: no names, emails, dates of birth, guardians or IDs;
- safety reports are only counted: no categories, tutors or reporters.
Staff and admin accounts are left out. Days run in South African time (TIME_ZONE), Monday to Sunday.
Agreed with the CEO on 30 Oct 2026 (Phanda Staff OS docs/PLAN-BRIGHTS.md, option A).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery, Sum
from django.utils import timezone

from accounts.rules import AccountType
from contact.models import ContactEvent
from moderation.models import Report
from profiles.models import ProfileViewDay
from tutors.models import ApplicationEvent, TutorApplication
from tutors.rules import Status


def _bounds(start: date, end: date) -> tuple[datetime, datetime]:
    tz = timezone.get_current_timezone()
    return (timezone.make_aware(datetime.combine(start, time.min), tz),
            timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), tz))


def _people():
    """Every account except staff and admins, and not suspended."""
    return get_user_model().objects.filter(is_staff=False, is_superuser=False, is_active=True)


def _value(v):
    return {"value": v}


def _unavailable(reason):
    return {"value": None, "reason": reason}


def _verified_tutors(at: datetime) -> int:
    """Tutors whose application stood at 'approved' at that moment, from the permanent decision history."""
    last_status = (ApplicationEvent.objects.filter(application=OuterRef("pk"), created_at__lt=at)
                   .order_by("-created_at", "-id").values("to_status")[:1])
    return (TutorApplication.objects.filter(user__in=_people())
            .annotate(status_then=Subquery(last_status)).filter(status_then=Status.APPROVED).count())


def collect(start: date, end: date) -> dict:
    a, b = _bounds(start, end)
    contacts = ContactEvent.objects.filter(created_at__gte=a, created_at__lt=b, requester__in=_people())
    requesters = contacts.values("requester_id").distinct()
    returning = (ContactEvent.objects.filter(requester_id__in=requesters, created_at__lt=a)
                 .values("requester_id").distinct().count())
    reports = Report.objects.filter(created_at__gte=a, created_at__lt=b)
    views = ProfileViewDay.objects.filter(date__gte=start, date__lte=end).aggregate(n=Sum("count"))["n"] or 0
    return {
        "registered-users": _value(_people().filter(account_type=AccountType.LEARNER, date_joined__lt=b).count()),
        "registered-parents": _value(_people().filter(account_type=AccountType.PARENT, date_joined__lt=b).count()),
        "verified-tutors": _value(_verified_tutors(b)),
        "tutor-applications": _value(
            ApplicationEvent.objects.filter(to_status=Status.PENDING, created_at__gte=a, created_at__lt=b,
                                            application__user__in=_people())
            .values("application_id").distinct().count()),
        "contacts-started": _value(contacts.count()),
        "returning-contacts": _value(returning),
        "profile-views": _value(views),
        "safety-reports": _value(reports.count()),
        "urgent-safety-reports": _value(reports.filter(is_urgent=True).count()),
        "lessons-booked": _unavailable("Brights doesn't record bookings yet (a contact isn't a lesson)."),
        "weekly-active-users": _unavailable("Brights keeps only each person's last login, so weekly use can't be "
                                            "counted."),
        "retention-4-weeks": _unavailable("Brights keeps only each person's last login, so returning use can't "
                                          "be counted."),
    }
