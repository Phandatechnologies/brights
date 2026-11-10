from django.apps import AppConfig


class StaffpanelConfig(AppConfig):
    """The Brights staff area (/staff in the web app): the friendly replacement for the Django admin."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "staffpanel"
