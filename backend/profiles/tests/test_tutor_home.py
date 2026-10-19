from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from contact.models import ContactEvent
from profiles.models import ProfileViewDay

from .test_api import ProfileTestCase


def make_person(email, account_type="learner", **extra):
    return User.objects.create_user(email=email, password="Sunflower-Maths-42", first_name="P", last_name="Q",
                                    date_of_birth=dob_for_age(30), account_type=account_type,
                                    email_verified_at=timezone.now(), **extra)


class PauseTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.make_tutor("pause@example.com")
        self.client.force_authenticate(self.profile.user)

    def set_accepting(self, value):
        response = self.client.patch(reverse("own-profile"), {"accepting_learners": value}, format="json")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_pausing_hides_tutor_and_unpausing_restores(self):
        body = self.set_accepting(False)
        self.assertFalse(body["accepting_learners"])
        self.assertFalse(body["is_listed"])
        self.assertEqual(body["missing_fields"], [])  # pausing isn't a missing field
        self.client.force_authenticate(None)
        self.assertEqual(self.search(), [])
        self.assertEqual(self.client.get(reverse("tutor-detail", args=[self.profile.pk])).status_code, 404)

        self.client.force_authenticate(self.profile.user)
        self.assertTrue(self.set_accepting(True)["is_listed"])
        self.client.force_authenticate(None)
        self.assertEqual(self.search(), [self.profile.pk])

    def test_paused_tutor_cannot_be_contacted(self):
        self.set_accepting(False)
        learner = make_person("l@example.com")
        self.client.force_authenticate(learner)
        response = self.client.post(reverse("contact-tutor", args=[self.profile.pk]),
                                    {"subject": self.maths.pk, "grade": 11}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_paused_tutor_can_still_be_reported_by_past_contacts(self):
        learner = make_person("past@example.com")
        ContactEvent.objects.create(requester=learner, tutor=self.profile, subject=self.maths, grade=11)
        self.set_accepting(False)
        self.client.force_authenticate(learner)
        response = self.client.post(reverse("report-tutor", args=[self.profile.pk]),
                                    {"category": "other", "description": "Something about lessons that needs review."},
                                    format="json")
        self.assertEqual(response.status_code, 201)


class ViewCountTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.make_tutor("views@example.com")
        self.url = reverse("tutor-detail", args=[self.profile.pk])

    def total(self):
        return sum(ProfileViewDay.objects.filter(profile=self.profile).values_list("count", flat=True))

    def test_each_visitor_counts_once_per_day(self):
        self.client.get(self.url)
        self.client.get(self.url)  # same anonymous visitor (same IP)
        self.assertEqual(self.total(), 1)
        self.client.get(self.url, REMOTE_ADDR="10.0.0.9")  # another visitor
        self.assertEqual(self.total(), 2)
        learner = make_person("viewer@example.com")
        self.client.force_authenticate(learner)
        self.client.get(self.url)
        self.client.get(self.url)
        self.assertEqual(self.total(), 3)

    def test_own_and_staff_views_do_not_count(self):
        self.client.force_authenticate(self.profile.user)
        self.client.get(self.url)
        staff = make_person("staff@example.com", account_type="", is_staff=True)
        self.client.force_authenticate(staff)
        self.client.get(self.url)
        self.assertEqual(self.total(), 0)

    def test_hidden_profiles_are_not_counted(self):
        self.profile.accepting_learners = False
        self.profile.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.total(), 0)

    def test_no_viewer_identity_is_stored(self):
        self.client.get(self.url)
        field_names = {f.name for f in ProfileViewDay._meta.get_fields()}
        self.assertEqual(field_names, {"id", "profile", "date", "count"})


class InsightsTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.make_tutor("numbers@example.com", subjects=((None, "approved", [10, 11, 12]),))
        self.url = reverse("own-insights")

    def test_only_tutors(self):
        self.client.force_authenticate(make_person("l@example.com"))
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_numbers_this_month_and_last_month(self):
        today = timezone.localdate()
        last_month_day = today.replace(day=1) - timedelta(days=3)
        ProfileViewDay.objects.create(profile=self.profile, date=today, count=7)
        ProfileViewDay.objects.create(profile=self.profile, date=last_month_day, count=4)

        a, b = make_person("a@example.com"), make_person("b@example.com", account_type="parent")
        ContactEvent.objects.create(requester=a, tutor=self.profile, subject=self.maths, grade=11)
        ContactEvent.objects.create(requester=a, tutor=self.profile, subject=self.maths, grade=11)  # same learner again
        ContactEvent.objects.create(requester=b, tutor=self.profile, subject=self.maths, grade=12)
        old = ContactEvent.objects.create(requester=b, tutor=self.profile, subject=self.maths, grade=12)
        ContactEvent.objects.filter(pk=old.pk).update(
            created_at=timezone.make_aware(timezone.datetime.combine(last_month_day, timezone.datetime.min.time()).replace(hour=12)))

        # Another tutor's numbers never leak in.
        other = self.make_tutor("other@example.com")
        ProfileViewDay.objects.create(profile=other, date=today, count=50)
        ContactEvent.objects.create(requester=a, tutor=other, subject=self.maths, grade=10)

        self.client.force_authenticate(self.profile.user)
        body = self.client.get(self.url).json()
        self.assertEqual(body["views_this_month"], 7)
        self.assertEqual(body["views_last_month"], 4)
        self.assertEqual(body["contacts_this_month"], 2)  # two different people
        self.assertEqual(body["contacts_last_month"], 1)
        self.assertEqual(body["contacts_all_time"], 2)
        self.assertEqual(body["top_requests"], [
            {"subject": "Mathematics", "grade": 11, "count": 2},
            {"subject": "Mathematics", "grade": 12, "count": 1},
        ])
        # Counts only: nothing that identifies a learner.
        self.assertNotIn("a@example.com", str(body))

    def test_new_tutor_without_profile_gets_zeros(self):
        tutor = make_person("fresh@example.com", account_type="tutor")
        self.client.force_authenticate(tutor)
        body = self.client.get(self.url).json()
        self.assertEqual((body["views_this_month"], body["contacts_this_month"], body["top_requests"]), (0, 0, []))
