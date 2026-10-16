"""Rules for public tutor profiles and search."""

import re

PROVINCES = [
    ("eastern_cape", "Eastern Cape"),
    ("free_state", "Free State"),
    ("gauteng", "Gauteng"),
    ("kwazulu_natal", "KwaZulu-Natal"),
    ("limpopo", "Limpopo"),
    ("mpumalanga", "Mpumalanga"),
    ("north_west", "North West"),
    ("northern_cape", "Northern Cape"),
    ("western_cape", "Western Cape"),
]

MIN_HOURLY_RATE = 50       # rands
MAX_HOURLY_RATE = 2000     # rands
MAX_BIO_LENGTH = 1000
MAX_PHOTO_BYTES = 3 * 1024 * 1024
PHOTO_MAX_SIDE = 800       # pixels; photos are resized down to this


class PhotoStatus:
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    CHOICES = [
        (NONE, "No photo"),
        (PENDING, "Waiting for approval"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]


def normalise_sa_mobile(raw: str) -> str | None:
    """
    Accepts '082 123 4567', '0821234567', '+27 82 123 4567' or '27821234567'
    and returns '+27821234567'. Returns None if it isn't a valid SA mobile number.
    """
    digits = re.sub(r"[\s\-()]", "", raw or "")
    if digits.startswith("+27"):
        digits = digits[3:]
    elif digits.startswith("27") and len(digits) == 11:
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]
    # SA mobile numbers: 9 digits after the country code, starting with 6, 7 or 8.
    if re.fullmatch(r"[678]\d{8}", digits):
        return "+27" + digits
    return None


CONTACT_DETAILS_MESSAGE = (
    "Please don't include phone numbers, emails, links or social media handles. "
    "Learners contact you safely through Brights."
)


def contains_contact_details(text: str) -> bool:
    """
    True if the text looks like it contains a phone number, email address, link or
    @handle. Tutors share their number only through the WhatsApp contact flow, which
    is logged and has protections for minors.
    """
    if not text:
        return False
    lowered = text.lower()
    digits_only = re.sub(r"[\s\-().+/]", "", text)
    if re.search(r"\d{9,}", digits_only):                      # 0821234567, 082 123 4567, +27 82…
        return True
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text):            # emails
        return True
    if re.search(r"(https?://|www\.|wa\.me|t\.me|\.co\.za|\.com\b)", lowered):  # links
        return True
    if re.search(r"(^|\s)@[a-z0-9_.]{2,}", lowered):            # @handles
        return True
    return False
