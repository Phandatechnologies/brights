"""Rules for contacting tutors on WhatsApp."""

from urllib.parse import quote

MAX_NEW_TUTORS_PER_DAY = 10   # distinct tutors one account can contact in 24 hours
SAFETY_GUIDANCE_VERSION = 1   # bump when the guidance text changes, so minors confirm it again


def whatsapp_url(number_e164: str, message: str) -> str:
    """'+27821234567' → 'https://wa.me/27821234567?text=...' (wa.me wants digits only)."""
    digits = number_e164.lstrip("+")
    return f"https://wa.me/{digits}?text={quote(message)}"


def opening_message(*, tutor_first_name, account_type, is_minor, subject_name=None, grade=None):
    """The pre-filled WhatsApp text. The sender can edit it before sending."""
    topic = subject_name or "tutoring"
    grade_text = f" (Grade {grade})" if grade else ""
    if account_type == "parent":
        return (f"Hi {tutor_first_name}, I found you on Brights. I'm looking for a tutor for my child "
                f"for {topic}{grade_text}.")
    if is_minor:
        who = f"a Grade {grade} learner" if grade else "a high school learner"
        return (f"Hi {tutor_first_name}, I'm {who} and I found you on Brights. "
                f"I'm looking for help with {topic}.")
    return f"Hi {tutor_first_name}, I found you on Brights and I'm looking for help with {topic}{grade_text}."
