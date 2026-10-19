from datetime import timedelta

from django.core import mail
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from contact.models import ContactEvent
from moderation import services
from moderation.models import Report
from profiles.models import TutorProfile
from tutors.models import ApplicationEvent, ApplicationSubject, Subject, TutorApplication

DESCRIPTION = "The tutor asked my child to keep their chats a secret from us."


def make_user(email, account_type="parent", age=40, **extra):
    return User.objects.create_user(email=email, password="Sunflower-Maths-42", first_name=email.split("@")[0].title(),
                                    last_name="Test", date_of_birth=dob_for_age(age), account_type=account_type,
                                    email_verified_at=timezone.now(), **extra)


@override_settings(REPORT_ALERT_EMAILS=["safety@brights.test"])
class ReportTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        tutor_user = make_user("sipho@example.com", "tutor", 24)
        app = TutorApplication.objects.create(user=tutor_user, pathway="academic", status="approved", reviewed_at=timezone.now())
        ApplicationSubject.objects.create(application=app, subject=Subject.objects.get(name="Mathematics"),
                                          matric_mark=80, grades=[10], decision="approved")
        self.tutor = TutorProfile.objects.create(user=tutor_user, bio="Maths", hourly_rate=200, teaches_online=True,
                                                 whatsapp_number="+27821234567", photo_status="approved")
        self.parent = make_user("parent@example.com")
        self.admin = User.objects.create_superuser(email="admin@example.com", password="Admin-Pass-91", first_name="Ada",
                                                   last_name="Admin", date_of_birth=dob_for_age(40))

    def report(self, user=None, category="inappropriate", tutor=None, **extra):
        self.client.force_authenticate(user or self.parent)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("report-tutor", args=[(tutor or self.tutor).pk]),
                                    {"category": category, "description": DESCRIPTION, **extra}, format="json")

    def search_ids(self):
        self.client.force_authenticate(None)
        return [r["id"] for r in self.client.get(reverse("tutor-search")).json()["results"]]


class SubmitTests(ReportTestCase):
    def test_logged_out_cannot_report(self):
        response = self.client.post(reverse("report-tutor", args=[self.tutor.pk]),
                                    {"category": "other", "description": DESCRIPTION}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_report_created_and_reporter_emailed(self):
        response = self.report()
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()["urgent"])
        report = Report.objects.get()
        self.assertEqual((report.reporter, report.tutor, report.status), (self.parent, self.tutor, "open"))
        self.assertEqual([m.to for m in mail.outbox], [["parent@example.com"]])
        self.assertIn("116", mail.outbox[0].body)  # Childline number

    def test_tutor_is_not_told(self):
        self.report()
        self.assertNotIn(["sipho@example.com"], [m.to for m in mail.outbox])

    def test_description_must_be_meaningful(self):
        self.client.force_authenticate(self.parent)
        response = self.client.post(reverse("report-tutor", args=[self.tutor.pk]),
                                    {"category": "other", "description": "bad"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_future_incident_date_rejected(self):
        response = self.report(incident_date=(timezone.localdate() + timedelta(days=2)).isoformat())
        self.assertEqual(response.status_code, 400)

    def test_one_open_report_per_tutor(self):
        self.report()
        self.assertEqual(self.report().status_code, 409)

    def test_daily_limit(self):
        for i in range(5):
            other = make_user(f"t{i}@example.com", "tutor", 25)
            app = TutorApplication.objects.create(user=other, pathway="academic", status="approved")
            ApplicationSubject.objects.create(application=app, subject=Subject.objects.get(name="Mathematics"),
                                              matric_mark=80, grades=[10], decision="approved")
            profile = TutorProfile.objects.create(user=other, bio="x", hourly_rate=100, teaches_online=True,
                                                  whatsapp_number="+27821234500", photo_status="approved")
            self.assertEqual(self.report(tutor=profile).status_code, 201)
        self.assertEqual(self.report().status_code, 429)

    def test_cannot_report_self(self):
        self.assertEqual(self.report(user=self.tutor.user).status_code, 400)


class UrgentHoldTests(ReportTestCase):
    def setUp(self):
        super().setUp()
        ContactEvent.objects.create(requester=self.parent, tutor=self.tutor)  # a real connection

    def test_child_safety_report_hides_tutor_and_alerts_admins(self):
        self.assertEqual(self.search_ids(), [self.tutor.pk])
        response = self.report(category="child_safety")
        self.assertTrue(response.json()["urgent"])
        self.assertTrue(response.json()["tutor_hidden"])
        self.assertEqual(self.search_ids(), [])
        self.assertEqual(self.client.get(reverse("tutor-detail", args=[self.tutor.pk])).status_code, 404)
        alert = [m for m in mail.outbox if m.to == ["safety@brights.test"]]
        self.assertEqual(len(alert), 1)
        self.assertIn("URGENT", alert[0].subject)
        self.assertNotIn(DESCRIPTION, alert[0].body)  # details stay in the admin, not in email

    def test_hidden_tutor_cannot_be_contacted(self):
        self.report(category="child_safety")
        self.client.force_authenticate(make_user("p2@example.com"))
        self.assertEqual(self.client.post(reverse("contact-tutor", args=[self.tutor.pk])).status_code, 404)

    def test_non_urgent_report_keeps_tutor_visible(self):
        self.report(category="scam")
        self.assertEqual(self.search_ids(), [self.tutor.pk])

    def test_dismissing_restores_tutor(self):
        self.report(category="child_safety")
        services.dismiss(Report.objects.get().pk, self.admin, "Misunderstanding; confirmed with parent.")
        self.assertEqual(self.search_ids(), [self.tutor.pk])

    def test_previous_contact_can_still_report_hidden_tutor(self):
        other = make_user("other@example.com")
        ContactEvent.objects.create(requester=other, tutor=self.tutor)
        self.report(user=other, category="child_safety")
        self.assertEqual(self.search_ids(), [])
        self.assertEqual(self.report(category="inappropriate").status_code, 201)

    def test_stranger_cannot_report_hidden_tutor(self):
        self.report(category="child_safety")
        stranger = make_user("stranger@example.com")
        self.assertEqual(self.report(user=stranger).status_code, 404)

    def test_child_safety_report_from_stranger_is_urgent_but_does_not_hide(self):
        stranger = make_user("stranger@example.com")
        response = self.report(user=stranger, category="child_safety")
        self.assertTrue(response.json()["urgent"])
        self.assertFalse(response.json()["tutor_hidden"])
        self.assertEqual(self.search_ids(), [self.tutor.pk])
        alert = [m for m in mail.outbox if m.to == ["safety@brights.test"]][0]
        self.assertIn("still visible", alert.body)

    def test_tutor_accounts_cannot_hide_other_tutors(self):
        rival = make_user("rival@example.com", "tutor", 30)
        ContactEvent.objects.create(requester=rival, tutor=self.tutor)  # even with a contact record
        self.report(user=rival, category="child_safety")
        self.assertEqual(self.search_ids(), [self.tutor.pk])


class ActionTests(ReportTestCase):
    def setUp(self):
        super().setUp()
        self.report()
        self.r = Report.objects.get()
        mail.outbox.clear()

    def test_dismiss_needs_notes_and_emails_reporter(self):
        with self.assertRaises(ValidationError):
            services.dismiss(self.r.pk, self.admin, "")
        with self.captureOnCommitCallbacks(execute=True):
            services.dismiss(self.r.pk, self.admin, "No evidence")
        self.r.refresh_from_db()
        self.assertEqual((self.r.status, self.r.outcome, self.r.closed_by), ("closed", "dismissed", self.admin))
        self.assertEqual([m.to for m in mail.outbox], [["parent@example.com"]])
        self.assertIn("finished reviewing", mail.outbox[0].body)

    def test_warn_emails_tutor_without_reporter_identity(self):
        with self.captureOnCommitCallbacks(execute=True):
            services.warn(self.r.pk, self.admin, "Keep all messages about schoolwork.")
        tutor_mail = [m for m in mail.outbox if m.to == ["sipho@example.com"]][0]
        self.assertIn("Keep all messages about schoolwork.", tutor_mail.body)
        self.assertNotIn("parent@example.com", tutor_mail.body)
        self.assertNotIn("Parent", tutor_mail.body)

    def test_suspend_uses_application_workflow_and_audit_trail(self):
        services.suspend(self.r.pk, self.admin, "Breach of conduct rules")
        application = TutorApplication.objects.get(user=self.tutor.user)
        self.assertEqual(application.status, "suspended")
        self.assertTrue(ApplicationEvent.objects.filter(application=application, action="suspended").exists())
        self.assertEqual(self.search_ids(), [])

    def test_closed_report_cannot_be_actioned_again(self):
        services.dismiss(self.r.pk, self.admin, "No evidence")
        with self.assertRaises(ValidationError):
            services.suspend(self.r.pk, self.admin, "x")

    def test_only_staff_and_not_about_themselves(self):
        with self.assertRaises(PermissionDenied):
            services.dismiss(self.r.pk, self.parent, "x")
        staff_tutor = self.tutor.user
        staff_tutor.is_staff = True
        staff_tutor.save()
        with self.assertRaises(PermissionDenied):
            services.dismiss(self.r.pk, staff_tutor, "x")


class AdminPageTests(ReportTestCase):
    def setUp(self):
        super().setUp()
        ContactEvent.objects.create(requester=self.parent, tutor=self.tutor)
        self.report(category="child_safety")
        self.r = Report.objects.get()

    def test_non_staff_redirected(self):
        self.client.force_login(self.parent)
        self.assertEqual(self.client.get(reverse("admin:moderation_report_review", args=[self.r.pk])).status_code, 302)

    def test_review_page_shows_report_and_contact_history(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin:moderation_report_review", args=[self.r.pk]))
        self.assertContains(response, DESCRIPTION)
        self.assertContains(response, "hidden from search")
        self.assertNotContains(response, "never contacted this tutor")

    def test_dismiss_from_page(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("admin:moderation_report_review", args=[self.r.pk]), {"action": "dismiss", "notes": "Checked"})
        self.r.refresh_from_db()
        self.assertEqual(self.r.status, "closed")

    def test_reports_cannot_be_deleted(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("admin:moderation_report_delete", args=[self.r.pk])).status_code, 403)
