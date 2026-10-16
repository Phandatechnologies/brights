import io
import shutil
import tempfile

from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from profiles.models import TutorProfile
from profiles.rules import contains_contact_details

PASSWORD = "Sunflower-Maths-42"


def make_user(email, account_type="tutor", **extra):
    return User.objects.create_user(email=email, password=PASSWORD, first_name="T", last_name="U",
                                    date_of_birth=dob_for_age(30), account_type=account_type,
                                    email_verified_at=timezone.now(), **extra)


class ContactDetailsDetectionTests(TestCase):
    def test_blocked(self):
        for text in ["WhatsApp me on 082 123 4567", "call +27 82 123 4567", "0821234567",
                     "email sipho@gmail.com", "see www.mysite.co.za", "https://wa.me/27821234567",
                     "follow me @sipho_tutor", "my site sipho.com"]:
            self.assertTrue(contains_contact_details(text), text)

    def test_allowed(self):
        for text in ["I got 85% in Maths in 2022.", "Grades 10-12, R250/hour", "Available Mon, Wed 15:00-17:00",
                     "I studied at TUT for 3 years."]:
            self.assertFalse(contains_contact_details(text), text)


class BioContactDetailsApiTests(APITestCase):
    def test_bio_with_number_rejected(self):
        tutor = make_user("t@example.com")
        self.client.force_authenticate(tutor)
        response = self.client.patch(reverse("own-profile"), {"bio": "Message me on 082 123 4567 for lessons"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("phone numbers", str(response.json()))


class LoginHardeningTests(APITestCase):
    def setUp(self):
        cache.clear()

    def login(self, email, password=PASSWORD):
        return self.client.post(reverse("auth-login"), {"email": email, "password": password}, format="json")

    def test_staff_cannot_use_api_login(self):
        User.objects.create_superuser(email="admin@example.com", password=PASSWORD, first_name="A", last_name="D",
                                      date_of_birth=dob_for_age(40))
        response = self.login("admin@example.com")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 403)

    # The per-IP limit (10/minute) is switched off here so only the per-account lockout is tested.
    @mock.patch("rest_framework.throttling.ScopedRateThrottle.allow_request", return_value=True)
    def test_account_locked_after_10_failures_even_with_right_password(self, _throttle):
        make_user("victim@example.com")
        for _ in range(10):
            self.login("victim@example.com", "wrong-password")
        self.assertEqual(self.login("victim@example.com").status_code, 400)  # locked for 15 minutes
        cache.clear()
        self.assertEqual(self.login("victim@example.com").status_code, 200)

    @mock.patch("rest_framework.throttling.ScopedRateThrottle.allow_request", return_value=True)
    def test_successful_login_resets_counter(self, _throttle):
        make_user("ok@example.com")
        for _ in range(5):
            self.login("ok@example.com", "wrong-password")
        self.assertEqual(self.login("ok@example.com").status_code, 200)
        self.client.logout()
        for _ in range(5):
            self.login("ok@example.com", "wrong-password")
        self.assertEqual(self.login("ok@example.com").status_code, 200)


class RequestSizeTests(TestCase):
    def test_oversized_body_rejected(self):
        response = self.client.generic("POST", "/api/auth/login/", b"x", CONTENT_LENGTH=str(9 * 1024 * 1024),
                                       content_type="application/json")
        self.assertEqual(response.status_code, 413)


class VerifyEmailEnumerationTests(APITestCase):
    def test_verified_uid_does_not_confirm_to_strangers(self):
        from accounts.tokens import encode_uid
        user = make_user("v@example.com")
        response = self.client.post(reverse("auth-verify-email"), {"uid": encode_uid(user), "token": "x-y"}, format="json")
        self.assertEqual(response.status_code, 400)


TEMP = tempfile.mkdtemp()


@override_settings(PRIVATE_MEDIA_ROOT=TEMP)
class PhotoApprovalRaceTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP, ignore_errors=True)

    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD, first_name="A",
                                                   last_name="D", date_of_birth=dob_for_age(40))
        self.tutor = make_user("pic@example.com")
        self.profile = TutorProfile.objects.create(user=self.tutor)
        self.upload()
        self.client.force_login(self.admin)
        self.url = reverse("admin:profiles_tutorprofile_changelist")

    def upload(self):
        out = io.BytesIO()
        Image.new("RGB", (50, 50), (1, 2, 3)).save(out, format="PNG")
        from rest_framework.test import APIClient
        c = APIClient()
        c.force_authenticate(self.tutor)
        c.post(reverse("own-photo"), {"photo": SimpleUploadedFile("p.png", out.getvalue())}, format="multipart")
        self.profile.refresh_from_db()

    def test_action_shows_photos_before_approving(self):
        response = self.client.post(self.url, {"action": "approve_photos", "_selected_action": [self.profile.pk]})
        self.assertContains(response, "Approve these photos")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "pending")

    def test_swapped_photo_is_not_approved_unseen(self):
        seen = self.profile.photo.name
        self.upload()  # tutor swaps the photo while the admin is looking
        self.client.post(self.url, {"action": "approve_photos", "_selected_action": [self.profile.pk],
                                    "confirm": "yes", f"seen_{self.profile.pk}": seen})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "pending")

    def test_seen_photo_is_approved(self):
        self.client.post(self.url, {"action": "approve_photos", "_selected_action": [self.profile.pk],
                                    "confirm": "yes", f"seen_{self.profile.pk}": self.profile.photo.name})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "approved")


class StaffDocumentPermissionTests(TestCase):
    def test_staff_without_document_permission_denied(self):
        staff = make_user("staff@example.com", account_type="", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("staff-document-download", args=[1]))
        self.assertEqual(response.status_code, 403)
