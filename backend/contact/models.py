from django.conf import settings
from django.db import models


class ContactEvent(models.Model):
    """
    A learner or parent revealed a tutor's WhatsApp number through Brights.
    Kept so the team can investigate reports (Phase 8) and spot misuse.
    """

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contacts_made")
    tutor = models.ForeignKey("profiles.TutorProfile", on_delete=models.CASCADE, related_name="contacts_received")
    subject = models.ForeignKey("tutors.Subject", null=True, blank=True, on_delete=models.SET_NULL)
    grade = models.PositiveSmallIntegerField(null=True, blank=True)
    requester_was_minor = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.requester} → {self.tutor.user} at {self.created_at:%Y-%m-%d %H:%M}"


class SafetyAcknowledgement(models.Model):
    """A learner under 18 confirmed they read the safety guidance before contacting tutors."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="safety_acknowledgements")
    version = models.PositiveSmallIntegerField()
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "version"], name="one_ack_per_version")]

    def __str__(self):
        return f"{self.user} acknowledged v{self.version}"
