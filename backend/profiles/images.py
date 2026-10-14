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

MAX_PIXELS = 40_000_000  # refuse absurdly large images (decompression-bomb protection)


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
            raise InvalidPhoto("That image is too large. Try a smaller photo.")
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise InvalidPhoto("Upload a JPG or PNG photo.")

    image = ImageOps.exif_transpose(image)          # keep the photo the right way up
    image = image.convert("RGB")                    # drops transparency and any embedded profiles
    image.thumbnail((PHOTO_MAX_SIDE, PHOTO_MAX_SIDE))

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)  # no EXIF is written
    return ContentFile(output.getvalue(), name="photo.jpg")
