from django.apps import AppConfig


class ModerationConfig(AppConfig):
    """Reports about tutors and how admins act on them."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "moderation"
