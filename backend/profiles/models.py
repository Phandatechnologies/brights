from django.conf import settings
from django.db import models

from tutors.uploads import get_private_storage

from .rules import PROVINCES, PhotoStatus


class Area(models.Model):
    """A general area tutors can be found in (never a street address). Admin-managed."""

    name = models.CharField(max_length=100)
    province = models.CharField(max_length=20, choices=PROVINCES)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["province", "name"]
        constraints = [models.UniqueConstraint(fields=["name", "province"], name="unique_area_per_province")]

    def __str__(self):
        return f"{self.name}, {self.get_province_display()}"


def photo_upload_path(instance, filename):
    import uuid
    return f"tutor-photos/{instance.user_id}/{uuid.uuid4().hex}.jpg"


class TutorProfile(models.Model):
    """
    What learners and parents see about a tutor. A tutor can fill it in at any
    time, but it only appears in search once their application is approved
    (see profiles/queries.py for the exact rules).
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tutor_profile")
    bio = models.TextField(blank=True)
    hourly_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Rands per hour")
    teaches_online = models.BooleanField(default=False)
    teaches_in_person = models.BooleanField(default=False)
    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.PROTECT)
    availability = models.CharField(max_length=300, blank=True, help_text="e.g. Weekday afternoons, Saturday mornings")

    # Private: only revealed through the WhatsApp contact flow (Phase 7), never in search.
    whatsapp_number = models.CharField(max_length=16, blank=True)

    # Optional photo: stored privately, shown publicly only once an admin approves it.
    photo = models.FileField(storage=get_private_storage, upload_to=photo_upload_path, blank=True, max_length=255)
    photo_status = models.CharField(max_length=20, choices=PhotoStatus.CHOICES, default=PhotoStatus.NONE)
    photo_note = models.CharField(max_length=300, blank=True, help_text="Reason shown to the tutor if rejected")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

    def missing_fields(self) -> list[str]:
        """What the tutor still needs to fill in before the profile can be shown."""
        missing = []
        if not self.bio.strip():
            missing.append("A short bio")
        if not self.hourly_rate:
            missing.append("Your hourly rate")
        if not (self.teaches_online or self.teaches_in_person):
            missing.append("Online and/or in-person lessons")
        if self.teaches_in_person and not self.area_id:
            missing.append("The area you tutor in")
        if not self.whatsapp_number:
            missing.append("Your WhatsApp number")
        return missing
