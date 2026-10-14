"""
Safe handling of verification documents.

- Only PDF, JPEG and PNG are accepted, identified by the file's first bytes
  ("magic numbers"), not by its name, so a renamed .exe can't get through.
- Files are stored under PRIVATE_MEDIA_ROOT, which is NOT served by any URL.
  The only way to download one is the staff-only view in tutors/views.py.
- Stored filenames are random; the original name is kept only for display.
"""

import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.signals import setting_changed
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

SIGNATURES = [
    (b"%PDF-", "application/pdf", "pdf"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
]


@deconstructible
class PrivateStorage(FileSystemStorage):
    """File storage with no public URL. Its folder is settings.PRIVATE_MEDIA_ROOT."""

    def __init__(self):
        super().__init__(base_url=None)

    @cached_property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    def url(self, name):
        raise NotImplementedError("Private files have no public URL.")


private_storage = PrivateStorage()


def _reset_private_storage(*, setting, **kwargs):
    """Let tests point PRIVATE_MEDIA_ROOT at a temporary folder with override_settings."""
    if setting == "PRIVATE_MEDIA_ROOT":
        for attr in ("base_location", "location"):
            private_storage.__dict__.pop(attr, None)


setting_changed.connect(_reset_private_storage)


def document_upload_path(instance, filename):
    """verification/<application id>/<random>.<ext> — the extension comes from the sniffed type."""
    ext = getattr(instance, "_detected_extension", "bin")
    return f"verification/{instance.application_id}/{uuid.uuid4().hex}.{ext}"


def sniff_file_type(uploaded_file):
    """Return (content_type, extension) from the file's first bytes, or (None, None)."""
    position = uploaded_file.tell()
    head = uploaded_file.read(16)
    uploaded_file.seek(position)
    for signature, content_type, extension in SIGNATURES:
        if head.startswith(signature):
            return content_type, extension
    return None, None


def safe_display_name(name: str) -> str:
    """Keep only the base name, strip control characters, cap the length."""
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = "".join(ch for ch in base if ch.isprintable()).strip()
    return (cleaned or "document")[:150]
