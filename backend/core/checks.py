from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, deploy=True)
def email_backend_check(app_configs, **kwargs):
    if "console" in settings.EMAIL_BACKEND or "locmem" in settings.EMAIL_BACKEND:
        return [Error(
            "EMAIL_BACKEND prints emails instead of sending them.",
            hint="Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend and the EMAIL_* values. "
                 "Otherwise password-reset links are written to the logs.",
            id="brights.E001",
        )]
    return []
