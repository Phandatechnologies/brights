import io
import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from profiles.models import Area, TutorProfile
from tutors.models import ApplicationSubject, Subject, TutorApplication

TEMP_MEDIA = tempfile.mkdtemp()


def png_bytes():
    out = io.BytesIO()
    Image.new("RGB", (300, 300), (10, 80, 200)).save(out, format="PNG")
    return out.getvalue()


@override_settings(PRIVATE_MEDIA_ROOT=TEMP_MEDIA)
class ProfileTestCase(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.maths = Subject.objects.get(name="Mathematics")
        self.english = Subject.objects.get(name="English Home Language")
        self.centurion = Area.objects.get(name="Centurion")
        self.soweto = Area.objects.get(name="Soweto")

    def make_tutor(self, email, *, status="approved", subjects=((None, "approved", [10, 11, 12]),),
                   rate=200, online=False, in_person=True, area=None, pathway="academic", **profile):
        user = User.objects.create_user(email=email, password="Sunflower-Maths-42", first_name="Tutor",
                                        last_name=email.split("@")[0].title(), date_of_birth=dob_for_age(23),
                                        account_type="tutor")
        app = TutorApplication.objects.create(user=user, pathway=pathway, status=status,
                                              submitted_at=timezone.now(), reviewed_at=timezone.now())
        for subject, decision, grades in subjects:
            ApplicationSubject.objects.create(application=app, subject=subject or self.maths, matric_mark=75,
                                              grades=list(grades), decision=decision)
        defaults = dict(bio="I love maths.", hourly_rate=rate, teaches_online=online, teaches_in_person=in_person,
                        area=area if area is not None else (self.centurion if in_person else None),
                        whatsapp_number="+27821234567",
                        photo_status="approved")  # listed tutors need an approved photo
        defaults.update(profile)
        return TutorProfile.objects.create(user=user, **defaults)

    def search(self, **params):
        response = self.client.get(reverse("tutor-search"), params)
        self.assertEqual(response.status_code, 200)
        return [r["id"] for r in response.json()["results"]]


class DiscoverabilityTests(ProfileTestCase):
    def test_approved_complete_tutor_is_listed_publicly(self):
        profile = self.make_tutor("ok@example.com")
        self.assertEqual(self.search(), [profile.pk])

    def test_non_approved_statuses_hidden(self):
        for status in ("draft", "pending", "more_info", "rejected", "suspended"):
            self.make_tutor(f"{status}@example.com", status=status)
        self.assertEqual(self.search(), [])

    def test_suspension_removes_tutor_and_profile_page(self):
        profile = self.make_tutor("s@example.com")
        TutorApplication.objects.filter(user=profile.user).update(status="suspended")
        self.assertEqual(self.search(), [])
        self.assertEqual(self.client.get(reverse("tutor-detail", args=[profile.pk])).status_code, 404)

    def test_deactivated_account_hidden(self):
        profile = self.make_tutor("d@example.com")
        User.objects.filter(pk=profile.user_id).update(is_active=False)
        self.assertEqual(self.search(), [])

    def test_incomplete_profile_hidden(self):
        self.make_tutor("nobio@example.com", bio="")
        self.make_tutor("nophone@example.com", whatsapp_number="")
        self.make_tutor("nomode@example.com", online=False, in_person=False)
        self.assertEqual(self.search(), [])

    def test_only_approved_subjects_shown(self):
        profile = self.make_tutor("mix@example.com", subjects=[(self.maths, "approved", [10]), (self.english, "declined", [8])])
        body = self.client.get(reverse("tutor-detail", args=[profile.pk])).json()
        self.assertEqual([s["name"] for s in body["subjects"]], ["Mathematics"])
        self.assertEqual(self.search(subject=self.english.pk), [])

    def test_no_approved_subjects_hidden(self):
        self.make_tutor("none@example.com", subjects=[(self.maths, "declined", [10])])
        self.assertEqual(self.search(), [])

    def test_private_details_never_exposed(self):
        profile = self.make_tutor("private@example.com")
        for url in (reverse("tutor-search"), reverse("tutor-detail", args=[profile.pk])):
            text = self.client.get(url).content.decode()
            for secret in ("+27821234567", "821234567", "private@example.com", "date_of_birth", "matric_mark", "75"):
                self.assertNotIn(secret, text, f"{secret} leaked from {url}")


class FilterTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.centurion_tutor = self.make_tutor("cent@example.com", rate=150, area=self.centurion)
        self.soweto_tutor = self.make_tutor("sow@example.com", rate=300, area=self.soweto,
                                            subjects=[(self.english, "approved", [8, 9])])
        self.online_tutor = self.make_tutor("online@example.com", rate=250, online=True, in_person=False)

    def test_subject_filter(self):
        self.assertEqual(sorted(self.search(subject=self.english.pk)), [self.soweto_tutor.pk])

    def test_grade_filter(self):
        self.assertEqual(sorted(self.search(grade=9)), [self.soweto_tutor.pk])
        self.assertEqual(sorted(self.search(grade=12)), sorted([self.centurion_tutor.pk, self.online_tutor.pk]))

    def test_area_includes_online_tutors_nationally(self):
        self.assertEqual(sorted(self.search(area=self.centurion.pk)), sorted([self.centurion_tutor.pk, self.online_tutor.pk]))

    def test_in_person_mode_excludes_online_only(self):
        self.assertEqual(self.search(area=self.centurion.pk, mode="in_person"), [self.centurion_tutor.pk])

    def test_online_mode(self):
        self.assertEqual(self.search(mode="online", area=self.soweto.pk), [self.online_tutor.pk])

    def test_province_filter(self):
        self.assertEqual(len(self.search(province="gauteng", mode="in_person")), 2)
        self.assertEqual(self.search(province="limpopo", mode="in_person"), [])

    def test_price_range_and_sort(self):
        self.assertEqual(self.search(min_price=200, max_price=280), [self.online_tutor.pk])
        self.assertEqual(self.search(sort="price_low"), [self.centurion_tutor.pk, self.online_tutor.pk, self.soweto_tutor.pk])

    def test_garbage_filters_ignored_safely(self):
        self.assertEqual(len(self.search(subject="abc", grade="x", min_price="cheap")), 3)


class OwnProfileTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.make_tutor("me@example.com", bio="", whatsapp_number="")
        self.client.force_authenticate(self.profile.user)
        self.url = reverse("own-profile")

    def test_only_tutors_can_edit_profiles(self):
        parent = User.objects.create_user(email="p@example.com", password="x-Long-Pass-1", first_name="P",
                                          last_name="P", date_of_birth=dob_for_age(40), account_type="parent")
        self.client.force_authenticate(parent)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_missing_fields_and_listing(self):
        body = self.client.get(self.url).json()
        self.assertFalse(body["is_listed"])
        self.assertIn("A short bio", body["missing_fields"])
        body = self.client.patch(self.url, {"bio": "Patient maths tutor.", "whatsapp_number": "082 123 4567"}, format="json").json()
        self.assertEqual(body["whatsapp_number"], "+27821234567")
        self.assertTrue(body["is_listed"])

    def test_own_profile_includes_public_id_and_id_is_read_only(self):
        self.assertEqual(self.client.get(self.url).json()["id"], self.profile.pk)
        response = self.client.patch(self.url, {"id": self.profile.pk + 999}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.profile.pk)

    def test_validation(self):
        bad = self.client.patch(self.url, {"hourly_rate": 10, "whatsapp_number": "012 345 6789"}, format="json")
        self.assertEqual(bad.status_code, 400)
        self.assertIn("hourly_rate", bad.json())
        self.assertIn("whatsapp_number", bad.json())

    def test_in_person_needs_area(self):
        response = self.client.patch(self.url, {"teaches_in_person": True, "area": None}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_cannot_approve_own_photo(self):
        TutorProfile.objects.filter(pk=self.profile.pk).update(photo_status="none")
        self.client.patch(self.url, {"photo_status": "approved"}, format="json")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "none")

    def test_photo_is_required_to_be_listed(self):
        body = self.client.patch(self.url, {"bio": "Patient maths tutor.", "whatsapp_number": "082 123 4567"}, format="json").json()
        self.assertTrue(body["is_listed"])
        for status, missing in (("none", True), ("rejected", True), ("pending", False)):
            TutorProfile.objects.filter(pk=self.profile.pk).update(photo_status=status)
            body = self.client.get(self.url).json()
            self.assertFalse(body["is_listed"], status)
            self.assertEqual("A profile photo" in body["missing_fields"], missing, status)
        self.client.force_authenticate(None)
        self.assertEqual(self.search(), [])


class PhotoTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.make_tutor("pic@example.com")
        self.client.force_authenticate(self.profile.user)

    def upload(self, content=None, name="me.png"):
        return self.client.post(reverse("own-photo"), {"photo": SimpleUploadedFile(name, content or png_bytes())},
                                format="multipart")

    def test_upload_goes_to_pending_and_is_not_public(self):
        self.assertEqual(self.upload().status_code, 201)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "pending")
        self.assertTrue(self.profile.photo.name.endswith(".jpg"))
        self.client.force_authenticate(None)
        # A photo is required to be listed, so while the new one waits for review the tutor is hidden.
        self.assertEqual(self.client.get(reverse("tutor-detail", args=[self.profile.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("tutor-photo", args=[self.profile.pk])).status_code, 404)

    def test_approved_photo_is_public(self):
        self.upload()
        TutorProfile.objects.filter(pk=self.profile.pk).update(photo_status="approved")
        self.client.force_authenticate(None)
        url = self.client.get(reverse("tutor-detail", args=[self.profile.pk])).json()["photo_url"]
        self.assertTrue(url.startswith(reverse("tutor-photo", args=[self.profile.pk])))
        response = self.client.get(reverse("tutor-photo", args=[self.profile.pk]))
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test_new_upload_needs_approval_again(self):
        self.upload()
        TutorProfile.objects.filter(pk=self.profile.pk).update(photo_status="approved")
        self.upload()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "pending")

    def test_owner_can_see_own_pending_photo(self):
        self.upload()
        self.assertEqual(self.client.get(reverse("own-photo")).status_code, 200)

    def test_fake_image_rejected(self):
        response = self.upload(b"MZ\x90 not an image", "me.jpg")
        self.assertEqual(response.status_code, 400)

    def test_staff_photo_view_is_staff_only(self):
        self.upload()
        url = reverse("staff-tutor-photo", args=[self.profile.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        admin = User.objects.create_superuser(email="a@example.com", password="Admin-Pass-91", first_name="A",
                                              last_name="D", date_of_birth=dob_for_age(40))
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_delete_photo(self):
        self.upload()
        self.assertEqual(self.client.delete(reverse("own-photo")).status_code, 204)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "none")


class AreaTests(ProfileTestCase):
    def test_areas_public_and_filterable(self):
        body = self.client.get(reverse("area-list"), {"province": "gauteng"}).json()
        self.assertEqual(len(body["provinces"]), 9)
        names = [a["name"] for a in body["areas"]]
        self.assertIn("Soshanguve", names)
