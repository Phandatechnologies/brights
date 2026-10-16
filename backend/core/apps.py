from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Shared, platform-wide pieces that don't belong to one feature (e.g. health check)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from . import checks  # noqa: F401  (registers deploy checks)
