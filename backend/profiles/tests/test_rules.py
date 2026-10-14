import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from profiles.images import InvalidPhoto, clean_photo
from profiles.rules import normalise_sa_mobile


class WhatsAppNumberTests(SimpleTestCase):
    def test_accepted_formats(self):
        for raw in ["082 123 4567", "0821234567", "+27 82 123 4567", "27821234567", "(082) 123-4567"]:
            self.assertEqual(normalise_sa_mobile(raw), "+27821234567", raw)

    def test_rejected_numbers(self):
        for raw in ["", "012 345 6789", "08212345", "+44 7700 900123", "hello"]:
            self.assertIsNone(normalise_sa_mobile(raw), raw)


def jpeg_with_gps():
    image = Image.new("RGB", (1600, 1200), (200, 120, 50))
    exif = Image.Exif()
    exif[0x8825] = {1: "S", 2: (25.0, 44.0, 0.0), 3: "E", 4: (28.0, 11.0, 0.0)}  # GPS info
    exif[0x010F] = "PhoneMaker"
    out = io.BytesIO()
    image.save(out, format="JPEG", exif=exif)
    return out.getvalue()


class PhotoCleaningTests(SimpleTestCase):
    def test_gps_and_exif_removed_and_resized(self):
        raw = jpeg_with_gps()
        self.assertIn(b"PhoneMaker", raw)  # sanity check: the test image really has EXIF
        cleaned = clean_photo(SimpleUploadedFile("me.jpg", raw)).read()
        image = Image.open(io.BytesIO(cleaned))
        self.assertEqual(len(image.getexif()), 0)
        self.assertNotIn(b"PhoneMaker", cleaned)
        self.assertLessEqual(max(image.size), 800)

    def test_non_image_rejected(self):
        with self.assertRaises(InvalidPhoto):
            clean_photo(SimpleUploadedFile("me.jpg", b"%PDF-1.4 not an image"))

    def test_gif_rejected(self):
        out = io.BytesIO()
        Image.new("RGB", (10, 10)).save(out, format="GIF")
        with self.assertRaises(InvalidPhoto):
            clean_photo(SimpleUploadedFile("me.gif", out.getvalue()))
