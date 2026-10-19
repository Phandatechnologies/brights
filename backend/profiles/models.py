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

    # The tutor's own on/off switch: off hides them from search and new contacts
    # (e.g. while they're full or on holiday) without changing anything else.
    accepting_learners = models.BooleanField(default=True)

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
        # Required to appear in search. A photo waiting for approval isn't "missing".
        if self.photo_status in (PhotoStatus.NONE, PhotoStatus.REJECTED):
            missing.append("A profile photo")
        return missing


class ProfileViewDay(models.Model):
    """
    How many times a tutor's public profile was viewed on one day. Only a number:
    who viewed it is never stored. A visitor counts once per profile per day.
    """

    profile = models.ForeignKey(TutorProfile, on_delete=models.CASCADE, related_name="view_days")
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "date"], name="one_view_counter_per_profile_per_day")]

    def __str__(self):
        return f"{self.profile} — {self.date}: {self.count}"


class GuideVideo(models.Model):
    """
    A how-to video for tutors (hosted on Brights' YouTube channel), shown on the tutor's Home.
    Staff add them in the admin by pasting the YouTube link.
    """

    class Topic(models.TextChoices):
        GETTING_STARTED = "getting_started", "Getting started"
        IN_PERSON = "in_person", "Tutoring in person"
        ONLINE = "online", "Tutoring online"

    title = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True, help_text="One or two sentences shown under the title.")
    topic = models.CharField(max_length=20, choices=Topic.choices, default=Topic.GETTING_STARTED)
    youtube_id = models.CharField(
        "YouTube link", max_length=200,  # room to paste a full link; clean() keeps just the ID
        help_text="Paste the video's YouTube link (e.g. https://youtu.be/…). Only the video ID is stored.",
    )
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers show first.")
    is_published = models.BooleanField(default=False, help_text="Tick when the video is public on YouTube.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError

        from .rules import youtube_video_id

        video_id = youtube_video_id(self.youtube_id)
        if not video_id:
            raise ValidationError({"youtube_id": "That doesn't look like a YouTube video link."})
        self.youtube_id = video_id
