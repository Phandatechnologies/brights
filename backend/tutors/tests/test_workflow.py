import shutil
import tempfile
from datetime import timedelta

from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from tutors import services
from tutors.models import ApplicationDocument, ApplicationEvent, ApplicationSubject, Subject, TutorApplication

TEMP_MEDIA = tempfile.mkdtemp()


def make_user(email, **extra):
    defaults = dict(password="Sunflower-Maths-42", first_name="Test", last_name="User",
                    date_of_birth=dob_for_age(25), account_type="tutor")
    defaults.update(extra)
    return User.objects.create_user(email=email, **defaults)


def make_admin(email="admin@example.com"):
    return User.objects.create_superuser(email=email, password="Admin-Pass-91", first_name="Ada",
                                         last_name="Admin", date_of_birth=dob_for_age(40))


@override_settings(PRIVATE_MEDIA_ROOT=TEMP_MEDIA)
class WorkflowTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.tutor = make_user("tutor@example.com", first_name="Sipho")
        self.admin = make_admin()
        self.app = TutorApplication.objects.create(user=self.tutor, pathway="academic", status="pending",
                                                   submitted_at=timezone.now())
        self.maths = ApplicationSubject.objects.create(
            application=self.app, subject=Subject.objects.get(name="Mathematics"), matric_mark=74, grades=[10, 11, 12])
        self.english = ApplicationSubject.objects.create(
            application=self.app, subject=Subject.objects.get(name="English Home Language"), matric_mark=65, grades=[8, 9])

    def approve_both(self):
        return {self.maths.pk: ("approved", ""), self.english.pk: ("approved", "")}

    def run_on_commit(self, fn, *args):
        with self.captureOnCommitCallbacks(execute=True):
            return fn(*args)


class ApproveTests(WorkflowTestCase):
    def test_approve_with_subject_decisions(self):
        decisions = {self.maths.pk: ("approved", ""), self.english.pk: ("declined", "Mark doesn't match statement")}
        self.run_on_commit(services.approve, self.app.pk, self.admin, decisions, "Welcome!")
        self.app.refresh_from_db(); self.maths.refresh_from_db(); self.english.refresh_from_db()
        self.assertEqual(self.app.status, "approved")
        self.assertEqual(self.app.reviewed_by, self.admin)
        self.assertEqual(self.maths.decision, "approved")
        self.assertEqual(self.english.decision, "declined")
        self.assertEqual(self.english.decision_note, "Mark doesn't match statement")

    def test_every_subject_needs_a_decision(self):
        with self.assertRaises(ValidationError):
            services.approve(self.app.pk, self.admin, {self.maths.pk: ("approved", "")})

    def test_declined_subject_needs_a_reason(self):
        with self.assertRaises(ValidationError):
            services.approve(self.app.pk, self.admin, {self.maths.pk: ("approved", ""), self.english.pk: ("declined", " ")})

    def test_at_least_one_subject_approved(self):
        with self.assertRaises(ValidationError):
            services.approve(self.app.pk, self.admin, {self.maths.pk: ("declined", "x"), self.english.pk: ("declined", "y")})

    def test_cannot_approve_subject_below_60(self):
        self.english.matric_mark = 59
        self.english.save()
        with self.assertRaises(ValidationError):
            services.approve(self.app.pk, self.admin, self.approve_both())

    def test_approval_emails_tutor_without_sensitive_details(self):
        self.run_on_commit(services.approve, self.app.pk, self.admin, self.approve_both())
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["tutor@example.com"])
        self.assertIn("approved", email.subject)
        self.assertNotIn("74", email.body)

    def test_event_recorded(self):
        services.approve(self.app.pk, self.admin, self.approve_both(), "Welcome")
        event = ApplicationEvent.objects.get(action="approved")
        self.assertEqual((event.from_status, event.to_status, event.actor), ("pending", "approved", self.admin))
        self.assertEqual(len(event.details), 2)


class PermissionTests(WorkflowTestCase):
    def test_non_staff_cannot_review(self):
        other_tutor = make_user("other@example.com")
        with self.assertRaises(PermissionDenied):
            services.approve(self.app.pk, other_tutor, self.approve_both())

    def test_admin_cannot_review_own_application(self):
        staff_tutor = make_user("staff.tutor@example.com", is_staff=True)
        own = TutorApplication.objects.create(user=staff_tutor, pathway="academic", status="pending")
        with self.assertRaises(PermissionDenied):
            services.reject(own.pk, staff_tutor, "no")

    def test_inactive_admin_cannot_review(self):
        self.admin.is_active = False
        self.admin.save()
        with self.assertRaises(PermissionDenied):
            services.reject(self.app.pk, self.admin, "no")


class TransitionTests(WorkflowTestCase):
    def test_request_info_needs_message_and_reopens_editing(self):
        with self.assertRaises(ValidationError):
            services.request_more_info(self.app.pk, self.admin, "")
        services.request_more_info(self.app.pk, self.admin, "Please upload a clearer ID")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "more_info")
        self.assertTrue(self.app.is_editable)

    def test_reject_needs_message(self):
        with self.assertRaises(ValidationError):
            services.reject(self.app.pk, self.admin, "   ")

    def test_cannot_skip_steps(self):
        with self.assertRaises(ValidationError):
            services.suspend(self.app.pk, self.admin, "Not approved yet")  # pending → suspended not allowed
        services.reject(self.app.pk, self.admin, "Documents unreadable")
        with self.assertRaises(ValidationError):
            services.approve(self.app.pk, self.admin, self.approve_both())  # rejected → approved not allowed

    def test_suspend_and_reinstate(self):
        services.approve(self.app.pk, self.admin, self.approve_both())
        services.suspend(self.app.pk, self.admin, "Report under investigation")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "suspended")
        services.reinstate(self.app.pk, self.admin, "Cleared")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "approved")
        actions = list(ApplicationEvent.objects.values_list("action", flat=True))
        self.assertEqual(actions, ["approved", "suspended", "reinstated"])

    def test_resubmission_resets_subject_decisions(self):
        services.request_more_info(self.app.pk, self.admin, "Clearer scan")
        self.maths.decision = "approved"
        self.maths.save()
        for kind in ("id_document", "matric_results"):
            ApplicationDocument.objects.create(application=self.app, kind=kind, file="x", original_name="x.pdf",
                                               content_type="application/pdf", size=1)
        services.submit(self.app.pk, self.tutor)
        self.maths.refresh_from_db()
        self.assertEqual(self.maths.decision, "pending")


class ReapplyTests(WorkflowTestCase):
    def setUp(self):
        super().setUp()
        services.reject(self.app.pk, self.admin, "Documents unreadable")

    def test_cannot_reapply_within_30_days(self):
        with self.assertRaises(ValidationError):
            services.reapply(self.app.pk, self.tutor)

    def test_can_reapply_after_30_days(self):
        TutorApplication.objects.filter(pk=self.app.pk).update(reviewed_at=timezone.now() - timedelta(days=31))
        services.reapply(self.app.pk, self.tutor)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "draft")
        self.assertEqual(self.app.reviewer_message, "")

    def test_api_reports_reapply_date(self):
        self.client.force_login(self.tutor)
        body = self.client.get(reverse("my-application")).json()
        self.assertIsNotNone(body["reapply_available_from"])
        response = self.client.post(reverse("application-reapply"))
        self.assertEqual(response.status_code, 400)


class AuditTrailProtectionTests(WorkflowTestCase):
    def test_events_cannot_be_changed_or_deleted_in_admin(self):
        services.reject(self.app.pk, self.admin, "No")
        self.client.force_login(self.admin)
        event = ApplicationEvent.objects.get()
        self.assertEqual(self.client.get(reverse("admin:tutors_applicationevent_delete", args=[event.pk])).status_code, 403)
        response = self.client.post(reverse("admin:tutors_applicationevent_change", args=[event.pk]), {"note": "edited"})
        event.refresh_from_db()
        self.assertEqual(event.note, "No")

    def test_application_with_history_cannot_be_deleted(self):
        from django.db.models import ProtectedError
        services.reject(self.app.pk, self.admin, "No")
        with self.assertRaises(ProtectedError):
            self.app.delete()

    def test_status_not_editable_in_change_form(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("admin:tutors_tutorapplication_change", args=[self.app.pk]), {"status": "approved"})
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "pending")


class AdminReviewPageTests(WorkflowTestCase):
    def url(self):
        return reverse("admin:tutors_tutorapplication_review", args=[self.app.pk])

    def test_non_staff_redirected_to_login(self):
        self.client.force_login(self.tutor)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_staff_sees_review_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertContains(response, "Mathematics")
        self.assertContains(response, "Approve selected subjects")

    def test_approve_from_review_page(self):
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url(), {
                "action": "approve",
                f"decision_{self.maths.pk}": "approved",
                f"decision_{self.english.pk}": "declined",
                f"note_{self.english.pk}": "Mark doesn't match",
                "message": "Welcome to Brights",
            })
        self.assertEqual(response.status_code, 302)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "approved")
        self.assertEqual(len(mail.outbox), 1)

    def test_errors_shown_and_status_unchanged(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {"action": "reject", "message": ""}, follow=True)
        self.assertContains(response, "Add a note")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "pending")
