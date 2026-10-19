import io
import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from tutors.models import ApplicationDocument, Subject, TutorApplication
from tutors.uploads import private_storage

PDF = b"%PDF-1.4\n% test document\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
TEMP_MEDIA = tempfile.mkdtemp()


def make_user(email, account_type="tutor", age=22, **extra):
    return User.objects.create_user(
        email=email, password="Sunflower-Maths-42", first_name="Test", last_name="User",
        date_of_birth=dob_for_age(age), account_type=account_type, email_verified_at=timezone.now(), **extra,
    )


def upload(name, content):
    return SimpleUploadedFile(name, content)


@override_settings(PRIVATE_MEDIA_ROOT=TEMP_MEDIA)
class ApplicationTestCase(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        assert str(private_storage.location) == TEMP_MEDIA  # never write test files to the real folder
        self.tutor = make_user("tutor@example.com")
        self.client.force_authenticate(self.tutor)
        self.maths = Subject.objects.get(name="Mathematics")
        self.english = Subject.objects.get(name="English Home Language")

    def start(self, pathway="academic"):
        return self.client.post(reverse("my-application"), {"pathway": pathway}, format="json")

    def set_subjects(self, subjects, **extra):
        return self.client.patch(reverse("my-application"), {"subjects": subjects, **extra}, format="json")

    def upload_doc(self, kind, name="doc.pdf", content=PDF):
        return self.client.post(
            reverse("document-upload"), {"kind": kind, "file": upload(name, content)}, format="multipart"
        )


class SubjectListTests(ApplicationTestCase):
    def test_subjects_are_public_and_seeded(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse("subject-list"))
        self.assertEqual(response.status_code, 200)
        names = [s["name"] for s in response.json()]
        self.assertIn("Mathematics", names)
        self.assertIn("isiZulu Home Language", names)

    def test_inactive_subjects_hidden(self):
        self.maths.is_active = False
        self.maths.save()
        names = [s["name"] for s in self.client.get(reverse("subject-list")).json()]
        self.assertNotIn("Mathematics", names)


class AccessTests(ApplicationTestCase):
    def test_logged_out_cannot_access(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("my-application")).status_code, 403)

    def test_learners_and_parents_cannot_apply(self):
        for account_type in ("learner", "parent"):
            user = make_user(f"{account_type}@example.com", account_type=account_type, age=30)
            self.client.force_authenticate(user)
            self.assertEqual(self.start().status_code, 403)

    def test_only_one_application(self):
        self.assertEqual(self.start().status_code, 201)
        self.assertEqual(self.start().status_code, 409)

    def test_new_application_is_a_draft(self):
        self.assertEqual(self.start().json()["status"], "draft")

    def test_unverified_tutor_cannot_start(self):
        self.tutor.email_verified_at = None
        self.tutor.save()
        response = self.start()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "email_unverified")
        self.assertFalse(TutorApplication.objects.filter(user=self.tutor).exists())


class SubjectRuleApiTests(ApplicationTestCase):
    def setUp(self):
        super().setUp()
        self.start()

    def test_mark_of_60_accepted(self):
        response = self.set_subjects([{"subject": self.maths.id, "matric_mark": 60, "grades": [10, 11, 12]}])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["subjects"][0]["grades"], [10, 11, 12])

    def test_mark_of_59_rejected(self):
        response = self.set_subjects([{"subject": self.english.id, "matric_mark": 59, "grades": [10]}])
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least 60%", str(response.json()))

    def test_grades_are_per_subject(self):
        response = self.set_subjects([
            {"subject": self.maths.id, "matric_mark": 80, "grades": [8, 9, 10, 11, 12]},
            {"subject": self.english.id, "matric_mark": 65, "grades": [8, 9]},
        ])
        grades = {s["subject"]["name"]: s["grades"] for s in response.json()["subjects"]}
        self.assertEqual(grades["Mathematics"], [8, 9, 10, 11, 12])
        self.assertEqual(grades["English Home Language"], [8, 9])

    def test_duplicate_subject_rejected(self):
        response = self.set_subjects([
            {"subject": self.maths.id, "matric_mark": 80, "grades": [10]},
            {"subject": self.maths.id, "matric_mark": 70, "grades": [11]},
        ])
        self.assertEqual(response.status_code, 400)

    def test_cannot_set_status_or_owner(self):
        other = make_user("other@example.com")
        self.client.patch(reverse("my-application"),
                          {"status": "approved", "user": other.id, "reviewer_message": "x"}, format="json")
        application = TutorApplication.objects.get(user=self.tutor)
        self.assertEqual(application.status, "draft")
        self.assertEqual(application.reviewer_message, "")

    def test_switching_to_academic_with_low_mark_blocked(self):
        self.client.patch(reverse("my-application"), {"pathway": "teacher"}, format="json")
        self.set_subjects([{"subject": self.maths.id, "grades": [8]}])
        response = self.client.patch(reverse("my-application"), {"pathway": "academic"}, format="json")
        self.assertEqual(response.status_code, 400)


class DocumentTests(ApplicationTestCase):
    def setUp(self):
        super().setUp()
        self.start()

    def test_pdf_upload_stored_privately_without_url(self):
        response = self.upload_doc("id_document", "my id.pdf")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["original_name"], "my id.pdf")
        self.assertNotIn("file", body)
        self.assertNotIn("url", str(body).lower())
        document = ApplicationDocument.objects.get()
        self.assertTrue(document.file.name.startswith(f"verification/{document.application_id}/"))
        self.assertTrue(document.file.name.endswith(".pdf"))
        self.assertNotIn("my id", document.file.name)

    def test_png_accepted(self):
        self.assertEqual(self.upload_doc("id_document", "scan.png", PNG).status_code, 201)

    def test_renamed_executable_rejected(self):
        response = self.upload_doc("id_document", "results.pdf", b"MZ\x90\x00 fake exe")
        self.assertEqual(response.status_code, 400)
        self.assertIn("PDF, JPG or PNG", str(response.json()))

    def test_oversized_file_rejected(self):
        big = PDF + b"0" * (5 * 1024 * 1024)
        self.assertEqual(self.upload_doc("id_document", "big.pdf", big).status_code, 400)

    def test_wrong_kind_for_pathway_rejected(self):
        self.assertEqual(self.upload_doc("sace_certificate").status_code, 400)

    def test_path_in_filename_is_stripped(self):
        self.upload_doc("id_document", "../../etc/passwd.pdf")
        self.assertEqual(ApplicationDocument.objects.get().original_name, "passwd.pdf")

    def test_tutor_cannot_delete_someone_elses_document(self):
        doc_id = self.upload_doc("id_document").json()["id"]
        intruder = make_user("intruder@example.com")
        self.client.force_authenticate(intruder)
        self.client.post(reverse("my-application"), {"pathway": "academic"}, format="json")
        response = self.client.delete(reverse("document-delete", args=[doc_id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ApplicationDocument.objects.filter(pk=doc_id).exists())

    def test_tutor_can_delete_own_document(self):
        doc_id = self.upload_doc("id_document").json()["id"]
        self.assertEqual(self.client.delete(reverse("document-delete", args=[doc_id])).status_code, 204)


class StaffDownloadTests(ApplicationTestCase):
    def setUp(self):
        super().setUp()
        self.start()
        self.doc_id = self.upload_doc("id_document", "id.pdf").json()["id"]
        self.url = reverse("staff-document-download", args=[self.doc_id])

    def test_owner_tutor_cannot_download(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_other_users_cannot_download(self):
        for user in (make_user("p@example.com", "parent", 40), make_user("l@example.com", "learner", 15,
                     guardian_name="G", )):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonymous_cannot_download(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_staff_can_download(self):
        staff = User.objects.create_superuser(
            email="admin@example.com", password="Admin-Pass-91", first_name="A", last_name="D",
            date_of_birth=dob_for_age(35),
        )
        self.client.force_authenticate(staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), PDF)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")


class SubmitTests(ApplicationTestCase):
    def setUp(self):
        super().setUp()
        self.start()

    def complete_academic(self):
        self.set_subjects([{"subject": self.maths.id, "matric_mark": 74, "grades": [10, 11, 12]}])
        self.upload_doc("id_document")
        self.upload_doc("matric_results")

    def test_incomplete_application_cannot_be_submitted(self):
        response = self.client.post(reverse("application-submit"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("subjects", response.json())
        self.assertIn("documents", response.json())

    def test_complete_application_submits_and_locks(self):
        self.complete_academic()
        response = self.client.post(reverse("application-submit"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "pending")
        self.assertFalse(response.json()["is_editable"])
        # Locked while pending:
        self.assertEqual(self.set_subjects([]).status_code, 409)
        self.assertEqual(self.upload_doc("id_document").status_code, 409)

    def test_more_info_required_unlocks_editing(self):
        self.complete_academic()
        self.client.post(reverse("application-submit"))
        TutorApplication.objects.filter(user=self.tutor).update(status="more_info", reviewer_message="Clearer scan please")
        response = self.client.get(reverse("my-application"))
        self.assertTrue(response.json()["is_editable"])
        self.assertEqual(response.json()["reviewer_message"], "Clearer scan please")
        self.assertEqual(self.upload_doc("id_document").status_code, 201)
        self.assertEqual(self.client.post(reverse("application-submit")).json()["status"], "pending")

    def test_teacher_pathway_requires_teacher_documents(self):
        self.client.patch(reverse("my-application"),
                          {"pathway": "teacher", "sace_number": "1234567", "qualification_name": "B.Ed"},
                          format="json")
        self.set_subjects([{"subject": self.maths.id, "grades": [8, 9]}])
        self.upload_doc("id_document")
        self.assertEqual(self.client.post(reverse("application-submit")).status_code, 400)
        self.upload_doc("teaching_qualification")
        self.upload_doc("sace_certificate")
        response = self.client.post(reverse("application-submit"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["subjects"][0]["matric_mark"])

    def test_academic_application_drops_teacher_details(self):
        response = self.client.patch(reverse("my-application"),
                                     {"sace_number": "999", "qualification_name": "X"}, format="json")
        self.assertEqual(response.json()["sace_number"], "")
