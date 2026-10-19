"""
Numbers for the tutor's Home: profile views and contacts. Counts only — the tutor
never learns who viewed their profile, and contacts are summarised, not listed.
"""

import hashlib
from datetime import date, timedelta

from django.core.cache import cache
from django.db.models import Count, F
from django.utils import timezone

from core.ip import client_ip

from .models import ProfileViewDay, TutorProfile

VIEW_DEDUP_SECONDS = 60 * 60 * 24  # one visitor counts once per profile per day


def _visitor_key(request) -> str:
    # Logged-in visitors by account, others by IP. Hashed so the cache never holds raw IPs.
    who = f"user:{request.user.pk}" if request.user.is_authenticated else f"ip:{client_ip(request)}"
    return hashlib.sha256(who.encode()).hexdigest()[:32]


def record_view(request, profile: TutorProfile) -> bool:
    """Count a public profile view. Returns True if it was counted."""
    user = request.user
    if user.is_authenticated and (user.pk == profile.user_id or user.is_staff):
        return False  # tutors previewing themselves and staff checks don't count
    today = timezone.localdate()
    key = f"profile-view:{profile.pk}:{today.isoformat()}:{_visitor_key(request)}"
    if not cache.add(key, 1, VIEW_DEDUP_SECONDS):  # add() is atomic: False if already counted
        return False
    counter, _ = ProfileViewDay.objects.get_or_create(profile=profile, date=today)
    ProfileViewDay.objects.filter(pk=counter.pk).update(count=F("count") + 1)
    return True


def _month_start(day: date) -> date:
    return day.replace(day=1)


def tutor_insights(profile: TutorProfile) -> dict:
    from contact.models import ContactEvent  # contact depends on profiles, not the other way round

    today = timezone.localdate()
    this_month = _month_start(today)
    last_month = _month_start(this_month - timedelta(days=1))

    def views_between(start, end=None):
        qs = ProfileViewDay.objects.filter(profile=profile, date__gte=start)
        if end:
            qs = qs.filter(date__lt=end)
        return sum(qs.values_list("count", flat=True))

    def learners_between(start, end=None):
        # Learners/parents who contacted the tutor (each counted once in the period).
        qs = ContactEvent.objects.filter(tutor=profile, created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lt=end)
        return qs.values("requester").distinct().count()

    requests = (
        ContactEvent.objects.filter(tutor=profile, created_at__date__gte=this_month, subject__isnull=False)
        .values(subject_name=F("subject__name"), grade_value=F("grade"))
        .annotate(count=Count("id"))
        .order_by("-count", "subject_name", "grade_value")[:5]
    )

    return {
        "month_label": today.strftime("%B %Y"),
        "views_this_month": views_between(this_month),
        "views_last_month": views_between(last_month, this_month),
        "contacts_this_month": learners_between(this_month),
        "contacts_last_month": learners_between(last_month, this_month),
        "contacts_all_time": ContactEvent.objects.filter(tutor=profile).values("requester").distinct().count(),
        "top_requests": [
            {"subject": r["subject_name"], "grade": r["grade_value"], "count": r["count"]} for r in requests
        ],
    }
