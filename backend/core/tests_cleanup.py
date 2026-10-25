import shutil
import tempfile
from io import StringIO
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from contact.models import ContactEvent
from moderation.models import Report
from profiles.models import TutorProfile
from tutors.models import ApplicationDocument, ApplicationEvent, Subject, TutorApplication
from tutors.uploads import private_storage

TEMP_MEDIA = tempfile.mkdtemp()


def person(email, account_type="parent", **extra):
    return User.objects.create_user(email=email, password="Sunflower-Maths-42", first_name="A", last_name="B",
                                    date_of_birth=dob_for_age(30), account_type=account_type, **extra)


@override_settings(PRIVATE_MEDIA_ROOT=TEMP_MEDIA)
class RemoveTestAccountsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.admin = User.objects.create_superuser(email="boss@example.com", password="Admin-Pass-91",
                                                   first_name="M", last_name="S", date_of_birth=dob_for_age(25))
        self.staff = person("helper@example.com", account_type="", is_staff=True)
        self.parent = person("parent@example.com")
        self.tutor = person("tutor@example.com", account_type="tutor")
        app = TutorApplication.objects.create(user=self.tutor, pathway="academic", status="approved",
                                              submitted_at=timezone.now())
        ApplicationEvent.objects.create(application=app, actor=self.admin, action="approve",
                                        from_status="pending", to_status="approved")
        self.doc = ApplicationDocument(application=app, kind="matric_results", original_name="r.pdf", size=13)
        self.doc.file.save("r.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
        self.profile = TutorProfile.objects.create(user=self.tutor, bio="x", hourly_rate=200, teaches_online=True,
                                                   whatsapp_number="+27821234567", photo_status="approved")
        self.profile.photo.save("p.jpg", ContentFile(b"\xff\xd8\xff test"), save=True)
        ContactEvent.objects.create(requester=self.parent, tutor=self.profile,
                                    subject=Subject.objects.get(name="Mathematics"), grade=10)
        Report.objects.create(reporter=self.parent, tutor=self.profile, category="other",
                              description="TEST report with enough words in it.")

    def run_cmd(self, *args, answer=None):
        out = StringIO()
        with patch("builtins.input", return_value=answer or ""):
            call_command("remove_test_accounts", *args, stdout=out)
        return out.getvalue()

    def test_dry_run_changes_nothing(self):
        out = self.run_cmd()
        self.assertIn("REMOVE  parent@example.com", out)
        self.assertIn("KEEP    boss@example.com", out)
        self.assertIn("Nothing was changed", out)
        self.assertEqual(User.objects.count(), 4)

    def test_wrong_confirmation_changes_nothing(self):
        with self.assertRaises(CommandError):
            self.run_cmd("--delete", answer="yes")
        self.assertEqual(User.objects.count(), 4)

    def test_delete_removes_test_accounts_and_their_data_but_keeps_staff(self):
        doc_name, photo_name = self.doc.file.name, self.profile.photo.name
        self.assertTrue(private_storage.exists(doc_name))
        with self.captureOnCommitCallbacks(execute=True):
            out = self.run_cmd("--delete", answer="DELETE 2")
        self.assertIn("Removed 2 account(s)", out)
        self.assertEqual(set(User.objects.values_list("email", flat=True)), {"boss@example.com", "helper@example.com"})
        for model in (TutorApplication, ApplicationEvent, ApplicationDocument, TutorProfile, ContactEvent, Report):
            self.assertEqual(model.objects.count(), 0, model.__name__)
        self.assertFalse(private_storage.exists(doc_name))
        self.assertFalse(private_storage.exists(photo_name))

    def test_keep_option_and_limit(self):
        out = self.run_cmd("--keep", "Parent@example.com")
        self.assertIn("KEEP    parent@example.com", out)
        with self.assertRaises(CommandError):
            self.run_cmd("--limit", "1")
