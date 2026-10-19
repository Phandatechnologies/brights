from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from contact.models import ContactEvent
from contact.rules import MAX_NEW_TUTORS_PER_DAY, opening_message, whatsapp_url
from profiles.models import Area, TutorProfile
from tutors.models import ApplicationSubject, Subject, TutorApplication


def make_user(email, account_type, age, **extra):
    return User.objects.create_user(email=email, password="Sunflower-Maths-42", first_name=email.split("@")[0].title(),
                                    last_name="Test", date_of_birth=dob_for_age(age), account_type=account_type,
                                    email_verified_at=timezone.now(), **extra)


class ContactTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.maths = Subject.objects.get(name="Mathematics")
        self.tutor = self.make_tutor("sipho@example.com", "+27821234567")
        self.parent = make_user("parent@example.com", "parent", 40)
        self.adult_learner = make_user("adult@example.com", "learner", 19)
        self.minor = make_user("minor@example.com", "learner", 15, guardian_name="G",
                               guardian_consent_given_at=timezone.now())

    def make_tutor(self, email, number, status="approved"):
        user = make_user(email, "tutor", 24)
        app = TutorApplication.objects.create(user=user, pathway="academic", status=status, reviewed_at=timezone.now())
        ApplicationSubject.objects.create(application=app, subject=self.maths, matric_mark=80, grades=[10, 11, 12],
                                          decision="approved")
        return TutorProfile.objects.create(user=user, bio="Maths tutor", hourly_rate=200, teaches_online=True,
                                           whatsapp_number=number, photo_status="approved")

    def contact(self, user, tutor=None, **data):
        self.client.force_authenticate(user)
        return self.client.post(reverse("contact-tutor", args=[(tutor or self.tutor).pk]), data, format="json")


class RuleTests(APITestCase):
    def test_whatsapp_url(self):
        url = whatsapp_url("+27821234567", "Hi Sipho, maths & science?")
        self.assertTrue(url.startswith("https://wa.me/27821234567?text="))
        self.assertEqual(parse_qs(urlparse(url).query)["text"][0], "Hi Sipho, maths & science?")

    def test_minor_message_identifies_learner(self):
        msg = opening_message(tutor_first_name="Sipho", account_type="learner", is_minor=True,
                              subject_name="Mathematics", grade=10)
        self.assertIn("Grade 10 learner", msg)

    def test_parent_message(self):
        msg = opening_message(tutor_first_name="Sipho", account_type="parent", is_minor=False,
                              subject_name="Mathematics", grade=11)
        self.assertIn("for my child", msg)


class WhoCanContactTests(ContactTestCase):
    def test_logged_out_cannot_get_number(self):
        response = self.client.post(reverse("contact-tutor", args=[self.tutor.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("821234567", response.content.decode())

    def test_parent_gets_link_and_contact_is_logged(self):
        response = self.contact(self.parent, subject=self.maths.pk, grade=11)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["whatsapp_url"].startswith("https://wa.me/27821234567"))
        self.assertIn("Mathematics (Grade 11)", response.json()["message"])
        event = ContactEvent.objects.get()
        self.assertEqual((event.requester, event.tutor, event.grade), (self.parent, self.tutor, 11))

    def test_tutors_and_staff_cannot_contact(self):
        other_tutor = self.make_tutor("t2@example.com", "+27831234567")
        self.assertEqual(self.contact(other_tutor.user).status_code, 403)
        staff = User.objects.create_superuser(email="a@example.com", password="Admin-Pass-91", first_name="A",
                                              last_name="D", date_of_birth=dob_for_age(40))
        self.assertEqual(self.contact(staff).status_code, 403)

    def test_suspended_tutor_cannot_be_contacted(self):
        TutorApplication.objects.filter(user=self.tutor.user).update(status="suspended")
        self.assertEqual(self.contact(self.parent).status_code, 404)
        self.assertFalse(ContactEvent.objects.exists())

    def test_subject_not_approved_for_tutor_is_ignored(self):
        english = Subject.objects.get(name="English Home Language")
        response = self.contact(self.parent, subject=english.pk, grade=10)
        self.assertNotIn("English", response.json()["message"])
        self.assertIsNone(ContactEvent.objects.get().subject)

    def test_grade_outside_tutor_range_is_ignored(self):
        self.contact(self.parent, subject=self.maths.pk, grade=8)
        self.assertIsNone(ContactEvent.objects.get().grade)


class MinorSafetyTests(ContactTestCase):
    def test_minor_must_acknowledge_safety_first(self):
        response = self.contact(self.minor)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "safety_ack_required")
        self.assertNotIn("821234567", response.content.decode())
        self.assertFalse(ContactEvent.objects.exists())

    def test_after_acknowledging_minor_can_contact(self):
        self.client.force_authenticate(self.minor)
        self.assertTrue(self.client.get(reverse("contact-safety")).json()["required"])
        self.client.post(reverse("contact-safety"))
        self.assertFalse(self.client.get(reverse("contact-safety")).json()["required"])
        response = self.contact(self.minor, subject=self.maths.pk, grade=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Grade 10 learner", response.json()["message"])
        self.assertTrue(ContactEvent.objects.get().requester_was_minor)

    def test_adults_do_not_need_safety_step(self):
        self.assertEqual(self.contact(self.adult_learner).status_code, 200)
        self.assertEqual(self.contact(self.parent).status_code, 200)


class LimitTests(ContactTestCase):
    def test_daily_limit_on_new_tutors(self):
        tutors = [self.make_tutor(f"t{i}@example.com", f"+278212300{i:02d}") for i in range(MAX_NEW_TUTORS_PER_DAY)]
        for t in tutors:
            self.assertEqual(self.contact(self.parent, t).status_code, 200)
        self.assertEqual(self.contact(self.parent).status_code, 429)
        # Re-contacting a tutor already contacted today is still allowed.
        self.assertEqual(self.contact(self.parent, tutors[0]).status_code, 200)

    def test_limit_resets_after_24_hours(self):
        tutors = [self.make_tutor(f"t{i}@example.com", f"+278212300{i:02d}") for i in range(MAX_NEW_TUTORS_PER_DAY)]
        for t in tutors:
            self.contact(self.parent, t)
        ContactEvent.objects.update(created_at=timezone.now() - timedelta(hours=25))
        self.assertEqual(self.contact(self.parent).status_code, 200)


class HistoryTests(ContactTestCase):
    def test_history_lists_contacted_tutors(self):
        self.contact(self.parent)
        self.contact(self.parent)
        body = self.client.get(reverse("contact-history")).json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["name"], "Sipho Test")
        self.assertTrue(body[0]["available"])

    def test_history_marks_unavailable_tutors(self):
        self.contact(self.parent)
        TutorApplication.objects.filter(user=self.tutor.user).update(status="suspended")
        body = self.client.get(reverse("contact-history")).json()
        self.assertFalse(body[0]["available"])

    def test_history_is_private(self):
        self.contact(self.parent)
        self.client.force_authenticate(self.adult_learner)
        self.assertEqual(self.client.get(reverse("contact-history")).json(), [])


class RealSessionTests(ContactTestCase):
    """Uses a real login session (not force_authenticate), like a browser does."""

    def test_contact_through_real_session(self):
        self.client.login(email="parent@example.com", password="Sunflower-Maths-42")
        response = self.client.post(reverse("contact-tutor", args=[self.tutor.pk]), {}, format="json")
        self.assertEqual(response.status_code, 200)
