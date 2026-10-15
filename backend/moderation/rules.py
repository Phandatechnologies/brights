"""Rules for reporting tutors."""


class Category:
    CHILD_SAFETY = "child_safety"
    INAPPROPRIATE = "inappropriate"
    FAKE_CREDENTIALS = "fake_credentials"
    SCAM = "scam"
    OTHER = "other"

    CHOICES = [
        (CHILD_SAFETY, "A safety concern involving a child"),
        (INAPPROPRIATE, "Inappropriate messages or behaviour"),
        (FAKE_CREDENTIALS, "Fake or misleading qualifications"),
        (SCAM, "Scam, no-show or payment problem"),
        (OTHER, "Something else"),
    ]

    # Reports in these categories hide the tutor from search until an admin reviews them.
    URGENT = {CHILD_SAFETY}


class ReportStatus:
    OPEN = "open"
    CLOSED = "closed"
    CHOICES = [(OPEN, "Open"), (CLOSED, "Closed")]


class Outcome:
    NONE = ""
    DISMISSED = "dismissed"
    WARNED = "warned"
    SUSPENDED = "suspended"
    CHOICES = [
        (NONE, "—"),
        (DISMISSED, "Dismissed (no action needed)"),
        (WARNED, "Tutor warned"),
        (SUSPENDED, "Tutor suspended"),
    ]


MIN_DESCRIPTION = 20
MAX_DESCRIPTION = 2000
MAX_REPORTS_PER_DAY = 5
