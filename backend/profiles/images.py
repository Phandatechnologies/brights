"""
Profile photo processing with Pillow.

Every photo is decoded and re-saved as a fresh JPEG. That:
  - proves the file really is an image (not something renamed),
  - removes EXIF metadata, which on phone photos often includes the GPS
    location where the photo was taken (frequently the tutor's home),
  - shrinks it to a sensible size.
"""

import io

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

from .rules import MAX_PHOTO_BYTES, PHOTO_MAX_SIDE

MAX_PIXELS = 12_000_000  # e.g. 4000 x 3000; refuse bigger (protects server memory)


class InvalidPhoto(ValueError):
    pass


def clean_photo(uploaded) -> ContentFile:
    if uploaded.size > MAX_PHOTO_BYTES:
        raise InvalidPhoto("Photos must be 3 MB or smaller.")
    try:
        image = Image.open(uploaded)
        if image.format not in ("JPEG", "PNG"):
            raise InvalidPhoto("Upload a JPG or PNG photo.")
        if image.width * image.height > MAX_PIXELS:
            raise InvalidPhoto("That image is too large. Try a smaller photo (under 12 megapixels).")
        if image.format == "JPEG":
            image.draft("RGB", (PHOTO_MAX_SIDE * 2, PHOTO_MAX_SIDE * 2))  # decode at reduced size
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise InvalidPhoto("Upload a JPG or PNG photo.")

    image.thumbnail((PHOTO_MAX_SIDE, PHOTO_MAX_SIDE))  # shrink first, so later steps use little memory
    image = ImageOps.exif_transpose(image)              # keep the photo the right way up
    image = image.convert("RGB")                        # drops transparency and any embedded profiles

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)  # no EXIF is written
    return ContentFile(output.getvalue(), name="photo.jpg")
