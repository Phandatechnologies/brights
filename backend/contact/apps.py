from django.apps import AppConfig


class ContactConfig(AppConfig):
    """Contacting tutors on WhatsApp: number reveal, contact log, limits and minor safety."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "contact"
