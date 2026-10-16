from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """User accounts, account types and authentication."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from . import backends  # noqa: F401  (connects the login-failure signal handlers)
