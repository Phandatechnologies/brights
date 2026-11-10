"""Staff area API: only staff get in, and every decision goes through the existing workflow."""

from datetime import timedelta

from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from tutors.models import ApplicationEvent, ApplicationSubject, Subject, TutorApplication


def make_user(email, **extra):
    defaults = dict(password="Sunflower-Maths-42", first_name="Test", last_name="User",
                    date_of_birth=dob_for_age(25), account_type="tutor", email_verified_at=timezone.now())
    defaults.update(extra)
    return User.objects.create_user(email=email, **defaults)


class StaffTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(email="admin@example.com", password="Admin-Pass-91",
                                                   first_name="Ada", last_name="Admin", date_of_birth=dob_for_age(40))
        self.tutor = make_user("sipho@example.com", first_name="Sipho", last_name="Nkosi")
        self.app = TutorApplication.objects.create(user=self.tutor, pathway="academic", status="pending",
                                                   submitted_at=timezone.now() - timedelta(days=3))
        self.maths = ApplicationSubject.objects.create(
            application=self.app, subject=Subject.objects.get(name="Mathematics"), matric_mark=74, grades=[10, 11, 12])
        self.english = ApplicationSubject.objects.create(
            application=self.app, subject=Subject.objects.get(name="English Home Language"), matric_mark=55, grades=[8, 9])
        self.client.force_authenticate(self.admin)

    def decide(self, app=None, **body):
        app = app or self.app
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("staff-application-decide", args=[app.pk]), body, format="json")


class AccessTests(StaffTestCase):
    def test_only_active_staff_get_in(self):
        urls = [reverse("staff-overview"), reverse("staff-applications"), reverse("staff-application", args=[self.app.pk])]
        for who in (None, self.tutor, make_user("parent@example.com", account_type="parent")):
            self.client.force_authenticate(who)
            for url in urls:
                self.assertIn(self.client.get(url).status_code, (401, 403), (who, url))
            response = self.client.post(reverse("staff-application-decide", args=[self.app.pk]), {"action": "reject", "message": "x"}, format="json")
            self.assertIn(response.status_code, (401, 403))
        blocked = User.objects.create_superuser(email="gone@example.com", password="Admin-Pass-91", first_name="G",
                                                last_name="One", date_of_birth=dob_for_age(40), is_active=False)
        self.client.force_authenticate(blocked)
        self.assertIn(self.client.get(urls[0]).status_code, (401, 403))
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "pending")

    def test_me_says_who_is_staff(self):
        self.assertTrue(self.client.get(reverse("auth-me")).json()["is_staff"])
        self.client.force_authenticate(self.tutor)
        self.assertFalse(self.client.get(reverse("auth-me")).json()["is_staff"])

    def test_is_staff_cannot_be_set_through_the_api(self):
        self.client.force_authenticate(self.tutor)
        self.client.patch(reverse("auth-me"), {"is_staff": True}, format="json")
        self.tutor.refresh_from_db()
        self.assertFalse(self.tutor.is_staff)


class OverviewTests(StaffTestCase):
    def test_counts(self):
        make_user("l@example.com", account_type="learner")
        make_user("p@example.com", account_type="parent")
        body = self.client.get(reverse("staff-overview")).json()
        self.assertEqual(body["applications_pending"], 1)
        self.assertEqual(body["oldest_pending_days"], 3)
        self.assertEqual(body["totals"], {"learners": 1, "parents": 1, "tutors": 1, "approved_tutors": 0})


class QueueTests(StaffTestCase):
    def test_waiting_queue_is_oldest_first_and_searchable(self):
        newer = TutorApplication.objects.create(user=make_user("lerato@example.com", first_name="Lerato"),
                                                pathway="teacher", status="pending", submitted_at=timezone.now())
        TutorApplication.objects.create(user=make_user("draft@example.com"), pathway="academic", status="draft")
        rows = self.client.get(reverse("staff-applications")).json()["results"]
        self.assertEqual([r["id"] for r in rows], [self.app.pk, newer.pk])
        self.assertEqual(rows[0]["days_waiting"], 3)
        self.assertEqual(rows[0]["subject_count"], 2)
        found = self.client.get(reverse("staff-applications"), {"q": "lerato"}).json()["results"]
        self.assertEqual([r["id"] for r in found], [newer.pk])
        drafts = self.client.get(reverse("staff-applications"), {"status": "draft"}).json()["results"]
        self.assertEqual(len(drafts), 1)
        everything = self.client.get(reverse("staff-applications"), {"status": "all"}).json()
        self.assertEqual(everything["count"], 3)


class DetailTests(StaffTestCase):
    def test_detail_has_what_a_reviewer_needs(self):
        body = self.client.get(reverse("staff-application", args=[self.app.pk])).json()
        self.assertEqual(body["name"], "Sipho Nkosi")
        self.assertEqual(body["actions"], ["approve", "request_info", "reject"])
        rows = {s["subject"]: s for s in body["subjects"]}
        self.assertFalse(rows["Mathematics"]["below_minimum"])
        self.assertTrue(rows["English Home Language"]["below_minimum"])
        self.assertTrue(body["can_view_documents"])

    def test_staff_without_document_permission_get_no_document_links(self):
        reviewer = make_user("rev@example.com", account_type="", is_staff=True)
        self.client.force_authenticate(reviewer)
        body = self.client.get(reverse("staff-application", args=[self.app.pk])).json()
        self.assertFalse(body["can_view_documents"])
        reviewer.user_permissions.add(Permission.objects.get(codename="view_applicationdocument"))
        reviewer = User.objects.get(pk=reviewer.pk)  # fresh permission cache
        self.client.force_authenticate(reviewer)
        self.assertTrue(self.client.get(reverse("staff-application", args=[self.app.pk])).json()["can_view_documents"])

    def test_no_actions_on_your_own_application(self):
        self.tutor.is_staff = True
        self.tutor.save()
        self.client.force_authenticate(self.tutor)
        self.assertEqual(self.client.get(reverse("staff-application", args=[self.app.pk])).json()["actions"], [])
        response = self.decide(action="reject", message="Nope")
        self.assertEqual(response.status_code, 403)


class DecisionTests(StaffTestCase):
    def test_approve_records_history_and_emails_tutor(self):
        response = self.decide(action="approve", message="Welcome!", decisions=[
            {"id": self.maths.pk, "decision": "approved"},
            {"id": self.english.pk, "decision": "declined", "note": "Below 60%"},
        ])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["status"], "approved")
        self.assertEqual(response.json()["actions"], ["suspend"])
        self.maths.refresh_from_db(); self.english.refresh_from_db()
        self.assertEqual((self.maths.decision, self.english.decision), ("approved", "declined"))
        event = ApplicationEvent.objects.get(application=self.app, action="approved")
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["sipho@example.com"])

    def test_rules_still_apply(self):
        # Below the minimum mark can't be approved; declining needs a reason; every subject needs a decision.
        response = self.decide(action="approve", decisions=[
            {"id": self.maths.pk, "decision": "approved"},
            {"id": self.english.pk, "decision": "approved"},
        ])
        self.assertEqual(response.status_code, 400)
        self.assertIn("English Home Language: can't be approved below 60%.", response.json()["non_field_errors"])
        response = self.decide(action="approve", decisions=[{"id": self.maths.pk, "decision": "approved"},
                                                            {"id": self.english.pk, "decision": "declined"}])
        self.assertIn("English Home Language: add a reason for declining.", response.json()["non_field_errors"])
        response = self.decide(action="approve", decisions=[{"id": self.maths.pk, "decision": "approved"}])
        self.assertIn("English Home Language: choose approve or decline.", response.json()["non_field_errors"])
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "pending")
        self.assertEqual(len(mail.outbox), 0)

    def test_request_info_and_reject_need_a_message(self):
        self.assertEqual(self.decide(action="request_info", message=" ").status_code, 400)
        response = self.decide(action="request_info", message="Your ID copy is blurry. Please upload a clearer one.")
        self.assertEqual(response.json()["status"], "more_info")
        self.assertEqual(len(mail.outbox), 1)

    def test_suspend_then_reinstate(self):
        self.decide(action="reject", message="Documents don't match.")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "rejected")
        self.assertEqual(self.decide(action="suspend", message="x").status_code, 400)  # wrong status

        other = TutorApplication.objects.create(user=make_user("ok@example.com"), pathway="teacher", status="approved")
        self.assertEqual(self.decide(other, action="suspend", message="").status_code, 400)  # reason needed
        self.assertEqual(self.decide(other, action="suspend", message="Under investigation.").json()["status"], "suspended")
        self.assertEqual(self.decide(other, action="reinstate").json()["status"], "approved")

    def test_unknown_action(self):
        self.assertEqual(self.decide(action="delete").status_code, 400)
        self.assertEqual(self.client.post(reverse("staff-application-decide", args=[999]), {"action": "reject"}, format="json").status_code, 404)
