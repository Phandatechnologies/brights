from django.conf import settings
from django.db import models

from .rules import Category, Outcome, ReportStatus


class Report(models.Model):
    """
    A report about a tutor. Never shown to the reported tutor.
    Kept permanently (PROTECT) because it may matter in a later investigation.
    """

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                 related_name="reports_made")
    tutor = models.ForeignKey("profiles.TutorProfile", on_delete=models.PROTECT, related_name="reports")
    category = models.CharField(max_length=30, choices=Category.CHOICES)
    description = models.TextField()
    incident_date = models.DateField(null=True, blank=True)
    is_urgent = models.BooleanField(default=False, db_index=True)
    # True when this report hides the tutor until it is closed: a child-safety report from a
    # learner or parent who contacted the tutor through Brights (prevents abuse by strangers).
    holds_tutor = models.BooleanField(default=False, db_index=True)
    reporter_was_minor = models.BooleanField(default=False)

    status = models.CharField(max_length=10, choices=ReportStatus.CHOICES, default=ReportStatus.OPEN, db_index=True)
    outcome = models.CharField(max_length=20, choices=Outcome.CHOICES, blank=True, default=Outcome.NONE)
    admin_notes = models.TextField(blank=True, help_text="Internal only. Never shown to the reporter or tutor.")
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_urgent", "created_at"]  # urgent first, then oldest first

    def __str__(self):
        return f"Report #{self.pk} on {self.tutor.user} ({self.get_category_display()})"
