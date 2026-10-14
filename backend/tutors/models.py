from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from .rules import DocumentKind, Pathway, Status, SubjectDecision
from .uploads import document_upload_path, private_storage


class Subject(models.Model):
    """A school subject tutors can offer. Managed by admins in the Django admin."""

    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TutorApplication(models.Model):
    """
    A tutor's request to be approved. One per tutor account.
    Only approved tutors will appear in search (Phase 6).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tutor_application"
    )
    pathway = models.CharField(max_length=20, choices=Pathway.CHOICES)
    status = models.CharField(max_length=20, choices=Status.CHOICES, default=Status.DRAFT)

    # Qualified-teacher pathway only.
    sace_number = models.CharField("SACE registration number", max_length=30, blank=True)
    qualification_name = models.CharField(max_length=200, blank=True)

    # Message from the review team that the tutor can see (e.g. what extra info is needed).
    reviewer_message = models.TextField(blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at", "-created_at"]

    @property
    def is_editable(self) -> bool:
        return self.status in Status.EDITABLE

    def __str__(self):
        return f"{self.user} ({self.get_status_display()})"


class ApplicationSubject(models.Model):
    """A subject the tutor wants to offer, the grades they'll teach it to, and their Matric mark."""

    application = models.ForeignKey(TutorApplication, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    matric_mark = models.PositiveSmallIntegerField(null=True, blank=True)  # academic pathway only
    grades = ArrayField(models.PositiveSmallIntegerField())

    # Set by the review team. Only approved subjects will be offered in search.
    decision = models.CharField(max_length=20, choices=SubjectDecision.CHOICES, default=SubjectDecision.PENDING)
    decision_note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["subject__name"]
        constraints = [
            models.UniqueConstraint(fields=["application", "subject"], name="unique_subject_per_application"),
            models.CheckConstraint(
                condition=models.Q(matric_mark__isnull=True) | models.Q(matric_mark__lte=100),
                name="matric_mark_at_most_100",
            ),
        ]

    def __str__(self):
        return f"{self.subject} {self.grades}"


class ApplicationDocument(models.Model):
    """A verification document. Stored privately; never exposed through public URLs."""

    application = models.ForeignKey(TutorApplication, on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(max_length=30, choices=DocumentKind.CHOICES)
    file = models.FileField(storage=private_storage, upload_to=document_upload_path, max_length=255)
    original_name = models.CharField(max_length=150)
    content_type = models.CharField(max_length=50)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.original_name}"


class ApplicationEvent(models.Model):
    """
    Permanent audit trail: every status change, who made it, and why.
    Never edited or deleted (the admin is read-only, and applications with
    history can't be deleted because of on_delete=PROTECT).
    """

    application = models.ForeignKey(TutorApplication, on_delete=models.PROTECT, related_name="events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    action = models.CharField(max_length=30)
    from_status = models.CharField(max_length=20, choices=Status.CHOICES)
    to_status = models.CharField(max_length=20, choices=Status.CHOICES)
    note = models.TextField(blank=True)
    # Snapshot of per-subject decisions at the time, e.g. [{"subject": "Mathematics", "decision": "approved"}]
    details = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.action}: {self.from_status} → {self.to_status}"
