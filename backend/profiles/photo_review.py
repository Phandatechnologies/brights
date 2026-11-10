"""
Approving and rejecting tutor profile photos (used by the staff area).

Safety rule kept from the admin version: a photo is only approved if it is still exactly
the photo the reviewer looked at. Each photo has a "version" (a hash of its stored name,
which changes on every upload), the review screen sends back the version it showed, and
a mismatch means the tutor replaced the photo meanwhile, so nothing is approved unseen.
"""

import hashlib

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import TutorProfile
from .rules import PhotoStatus

MAX_NOTE = 300


def photo_version(profile) -> str:
    return hashlib.sha256(profile.photo.name.encode()).hexdigest()[:16] if profile.photo else ""


def _lock(profile_id, staff, seen):
    if not (staff and staff.is_active and staff.is_staff):
        raise PermissionDenied("Only the Brights team can review photos.")
    profile = TutorProfile.objects.select_for_update().get(pk=profile_id)
    if profile.user_id == staff.pk:
        raise PermissionDenied("Another team member has to review your own photo.")
    if not profile.photo:
        raise ValidationError("This tutor has removed their photo.")
    if seen != photo_version(profile):
        raise ValidationError("The tutor changed this photo while you were looking. Check the new one.")
    return profile


@transaction.atomic
def approve(profile_id, staff, seen):
    profile = _lock(profile_id, staff, seen)
    profile.photo_status = PhotoStatus.APPROVED
    profile.photo_note = ""
    profile.save(update_fields=["photo_status", "photo_note", "updated_at"])
    return profile


@transaction.atomic
def reject(profile_id, staff, seen, note):
    note = (note or "").strip()
    if not note:
        raise ValidationError("Tell the tutor why, so they can upload a better photo.")
    if len(note) > MAX_NOTE:
        raise ValidationError(f"Keep the reason under {MAX_NOTE} characters.")
    profile = _lock(profile_id, staff, seen)
    profile.photo_status = PhotoStatus.REJECTED
    profile.photo_note = note
    profile.save(update_fields=["photo_status", "photo_note", "updated_at"])
    return profile
