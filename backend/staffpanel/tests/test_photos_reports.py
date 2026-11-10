"""Staff area: photo approval and safety reports go through the same rules as before."""

from django.core import mail
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from contact.models import ContactEvent
from moderation.models import Report
from profiles.models import TutorProfile
from tutors.models import ApplicationSubject, Subject, TutorApplication

from .test_applications import StaffTestCase, make_user

JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c"
    "20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100ffc4001f0000010501010101010100"
    "000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114"
    "328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a63646566"
    "6768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3"
    "d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbd3ffd9")


def tutor_with_photo(email="lerato@example.com", status="pending"):
    user = make_user(email, first_name="Lerato", last_name="Mahlangu")
    profile = TutorProfile.objects.create(user=user, bio="Science", hourly_rate=200, teaches_in_person=True,
                                          whatsapp_number="+27710000002", photo_status=status)
    profile.photo.save("photo.jpg", ContentFile(JPEG), save=True)
    TutorProfile.objects.filter(pk=profile.pk).update(photo_status=status)
    profile.refresh_from_db()
    return profile


class PhotoTests(StaffTestCase):
    def setUp(self):
        super().setUp()
        self.profile = tutor_with_photo()

    def queue(self, status="pending"):
        return self.client.get(reverse("staff-photos"), {"status": status}).json()["results"]

    def decide(self, **body):
        return self.client.post(reverse("staff-photo-decide", args=[self.profile.pk]), body, format="json")

    def test_queue_and_photo(self):
        rows = self.queue()
        self.assertEqual([r["name"] for r in rows], ["Lerato Mahlangu"])
        self.assertEqual(self.client.get(rows[0]["photo_url"]).status_code, 200)
        self.assertEqual(self.client.get(reverse("staff-overview")).json()["photos_waiting"], 1)

    def test_approve(self):
        version = self.queue()[0]["version"]
        response = self.decide(action="approve", version=version)
        self.assertEqual(response.json()["photo_status"], "approved")
        self.assertEqual(self.queue(), [])

    def test_reject_needs_a_reason_the_tutor_sees(self):
        version = self.queue()[0]["version"]
        self.assertEqual(self.decide(action="reject", version=version, note=" ").status_code, 400)
        self.decide(action="reject", version=version, note="Please use a clear photo of your face.")
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.photo_status, self.profile.photo_note), ("rejected", "Please use a clear photo of your face."))
        self.client.force_authenticate(self.profile.user)
        own = self.client.get(reverse("own-profile")).json()
        self.assertEqual(own["photo_note"], "Please use a clear photo of your face.")

    def test_photo_swapped_during_review_is_not_approved(self):
        row = self.queue()[0]
        self.profile.photo.save("photo.jpg", ContentFile(JPEG), save=True)  # tutor uploads a new photo
        response = self.decide(action="approve", version=row["version"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("changed this photo", response.json()["non_field_errors"][0])
        self.assertEqual(self.client.get(row["photo_url"]).status_code, 409)  # old link won't show the new photo
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo_status, "pending")

    def test_no_reviewing_your_own_photo(self):
        self.profile.user.is_staff = True
        self.profile.user.save()
        self.client.force_authenticate(self.profile.user)
        self.assertEqual(self.decide(action="approve", version=self.queue()[0]["version"]).status_code, 403)

    def test_only_staff(self):
        self.client.force_authenticate(self.profile.user)
        self.assertEqual(self.client.get(reverse("staff-photos")).status_code, 403)
        self.assertEqual(self.decide(action="approve", version="x").status_code, 403)


@override_settings(REPORT_ALERT_EMAILS=["safety@brights.test"])
class ReportTests(StaffTestCase):
    def setUp(self):
        super().setUp()
        self.app.status = "approved"
        self.app.save()
        self.maths.decision = "approved"  # an approved subject, so the tutor is listed in search
        self.maths.save()
        self.tutor_profile = TutorProfile.objects.create(user=self.tutor, bio="Maths", hourly_rate=200, teaches_online=True,
                                                         whatsapp_number="+27710000001", photo_status="approved")
        self.parent = make_user("thandi@example.com", account_type="parent", first_name="Thandi")
        ContactEvent.objects.create(requester=self.parent, tutor=self.tutor_profile, subject=Subject.objects.get(name="Mathematics"), grade=11)
        self.normal = Report.objects.create(reporter=self.parent, tutor=self.tutor_profile, category="scam",
                                            description="He took the money and never came to the lesson.")
        self.urgent = Report.objects.create(reporter=self.parent, tutor=self.tutor_profile, category="child_safety",
                                            description="Asked my child to keep their chats secret.", is_urgent=True, holds_tutor=True)

    def decide(self, report, **body):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("staff-report-decide", args=[report.pk]), body, format="json")

    def test_queue_urgent_first_and_counts(self):
        rows = self.client.get(reverse("staff-reports")).json()["results"]
        self.assertEqual([r["id"] for r in rows], [self.urgent.pk, self.normal.pk])
        overview = self.client.get(reverse("staff-overview")).json()
        self.assertEqual((overview["reports_open"], overview["reports_urgent"]), (2, 1))

    def test_detail_has_context(self):
        body = self.client.get(reverse("staff-report", args=[self.urgent.pk])).json()
        self.assertEqual(body["reporter"]["email"], "thandi@example.com")
        self.assertEqual(body["contacts"][0]["subject"], "Mathematics")
        self.assertEqual([r["id"] for r in body["other_reports"]], [self.normal.pk])
        self.assertEqual(body["actions"], ["dismiss", "warn", "suspend"])

    def test_dismiss_needs_internal_note(self):
        self.assertEqual(self.decide(self.normal, action="dismiss").status_code, 400)
        body = self.decide(self.normal, action="dismiss", notes="Lesson happened; parent confirmed.").json()
        self.assertEqual((body["status"], body["outcome"], body["actions"]), ("closed", "dismissed", []))
        self.assertIn("parent confirmed", body["admin_notes"])
        self.assertEqual([m.to for m in mail.outbox], [["thandi@example.com"]])  # reporter told it's reviewed
        self.assertEqual(self.decide(self.normal, action="dismiss", notes="again").status_code, 400)  # already closed

    def test_warn_emails_tutor(self):
        self.assertEqual(self.decide(self.normal, action="warn").status_code, 400)
        self.decide(self.normal, action="warn", message="Always confirm lessons in writing.")
        self.assertIn(["sipho@example.com"], [m.to for m in mail.outbox])

    def test_suspend_suspends_the_tutor_application(self):
        body = self.decide(self.urgent, action="suspend", message="We are investigating a safety concern.").json()
        self.assertEqual(body["outcome"], "suspended")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "suspended")
        self.assertEqual(body["tutor"]["application_status"], "suspended")

    def test_no_handling_reports_about_yourself(self):
        self.tutor.is_staff = True
        self.tutor.save()
        self.client.force_authenticate(self.tutor)
        self.assertEqual(self.client.get(reverse("staff-report", args=[self.normal.pk])).json()["actions"], [])
        self.assertEqual(self.decide(self.normal, action="dismiss", notes="Fine").status_code, 403)

    def test_urgent_alert_links_to_staff_area(self):
        Report.objects.filter(pk=self.urgent.pk).delete()  # an open child-safety report hides the tutor
        other_parent = make_user("naledi@example.com", account_type="parent")
        self.client.force_authenticate(other_parent)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("report-tutor", args=[self.tutor_profile.pk]),
                                        {"category": "child_safety", "description": "Asked my child to meet alone after class."}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        alert = next(m for m in mail.outbox if m.to == ["safety@brights.test"])
        self.assertIn("/staff/reports/", alert.body)

    def test_only_staff(self):
        self.client.force_authenticate(self.parent)
        self.assertEqual(self.client.get(reverse("staff-reports")).status_code, 403)
        self.assertEqual(self.client.get(reverse("staff-report", args=[self.normal.pk])).status_code, 403)
