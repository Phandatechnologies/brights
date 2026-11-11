"""Staff area: accounts (block, unblock, resend confirmation) and how-to videos."""

from django.contrib.admin.models import LogEntry
from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from profiles.models import GuideVideo

from .test_applications import StaffTestCase, make_user


class PeopleTests(StaffTestCase):
    def act(self, user, **body):
        return self.client.post(reverse("staff-user-action", args=[user.pk]), body, format="json")

    def test_list_filters_and_search(self):
        learner = make_user("kid@example.com", account_type="learner", first_name="Lwazi", date_of_birth=dob_for_age(15))
        rows = self.client.get(reverse("staff-users"), {"type": "learner"}).json()["results"]
        self.assertEqual([r["email"] for r in rows], ["kid@example.com"])
        self.assertTrue(rows[0]["is_minor"])
        self.assertEqual([r["id"] for r in self.client.get(reverse("staff-users"), {"q": "lwazi"}).json()["results"]], [learner.pk])
        staff_rows = self.client.get(reverse("staff-users"), {"type": "staff"}).json()["results"]
        self.assertEqual([r["account_type_label"] for r in staff_rows], ["Brights team"])

    def test_detail(self):
        body = self.client.get(reverse("staff-user", args=[self.tutor.pk])).json()
        self.assertEqual(body["tutor"]["application_status"], "pending")
        self.assertEqual(body["actions"], ["block"])
        self.assertNotIn("password", str(body))

    def test_block_needs_reason_logs_out_and_records_history(self):
        session = APIClient()
        session.force_login(self.tutor)
        self.assertEqual(session.get(reverse("auth-me")).status_code, 200)
        self.assertEqual(self.act(self.tutor, action="block").status_code, 400)
        body = self.act(self.tutor, action="block", reason="Shared fake documents").json()
        self.assertFalse(body["is_active"])
        self.assertEqual(body["actions"], ["unblock"])
        self.assertEqual(session.get(reverse("auth-me")).status_code, 403)  # their session stopped working
        login = APIClient().post(reverse("auth-login"), {"email": self.tutor.email, "password": "Sunflower-Maths-42"}, format="json")
        self.assertNotEqual(login.status_code, 200)
        self.assertEqual(body["history"][0]["what"], "Blocked login: Shared fake documents")
        self.assertEqual(body["history"][0]["by"], "admin@example.com")
        self.assertTrue(LogEntry.objects.filter(object_id=str(self.tutor.pk)).exists())  # also in the Django admin
        body = self.act(self.tutor, action="unblock").json()
        self.assertTrue(body["is_active"])

    def test_guardrails(self):
        self.assertEqual(self.act(self.admin, action="block", reason="x").status_code, 403)  # not yourself
        reviewer = make_user("rev@example.com", account_type="", is_staff=True)
        other_staff = make_user("other@example.com", account_type="", is_staff=True)
        self.client.force_authenticate(reviewer)
        self.assertEqual(self.act(other_staff, action="block", reason="x").status_code, 403)  # staff vs staff: owner only
        self.assertEqual(self.client.get(reverse("staff-user", args=[other_staff.pk])).json()["actions"], [])
        self.assertEqual(self.act(self.tutor, action="block", reason="Fake ID").status_code, 200)  # ordinary accounts: fine
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.act(other_staff, action="block", reason="Left the team").status_code, 200)  # owner can

    def test_resend_confirmation(self):
        unconfirmed = make_user("new@example.com", account_type="parent", email_verified_at=None)
        self.assertIn("resend_confirmation", self.client.get(reverse("staff-user", args=[unconfirmed.pk])).json()["actions"])
        self.assertEqual(self.act(unconfirmed, action="resend_confirmation").status_code, 200)
        self.assertEqual(mail.outbox[-1].to, ["new@example.com"])
        self.assertEqual(self.act(self.tutor, action="resend_confirmation").status_code, 400)  # already confirmed

    def test_only_staff(self):
        self.client.force_authenticate(self.tutor)
        self.assertEqual(self.client.get(reverse("staff-users")).status_code, 403)
        self.assertEqual(self.act(self.admin, action="block", reason="x").status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)


class VideoTests(StaffTestCase):
    def test_add_edit_publish_delete(self):
        response = self.client.post(reverse("staff-videos"), {
            "title": "Your first online lesson", "topic": "online", "youtube_id": "https://youtu.be/dQw4w9WgXcQ?t=10",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        video = response.json()
        self.assertEqual((video["youtube_id"], video["is_published"]), ("dQw4w9WgXcQ", False))  # draft by default
        tutor_view = APIClient()
        tutor_view.force_authenticate(self.tutor)
        self.assertEqual(tutor_view.get(reverse("tutor-guides")).json()["videos"], [])  # drafts stay hidden

        response = self.client.patch(reverse("staff-video", args=[video["id"]]), {"is_published": True, "order": 2}, format="json")
        self.assertEqual((response.json()["is_published"], response.json()["order"]), (True, 2))
        self.assertEqual([v["title"] for v in tutor_view.get(reverse("tutor-guides")).json()["videos"]], ["Your first online lesson"])

        self.assertEqual(self.client.delete(reverse("staff-video", args=[video["id"]])).status_code, 204)
        self.assertFalse(GuideVideo.objects.exists())

    def test_rejects_non_youtube_links(self):
        response = self.client.post(reverse("staff-videos"), {"title": "Bad", "topic": "online", "youtube_id": "https://evil.example.com/x"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("youtube_id", response.json())
        response = self.client.post(reverse("staff-videos"), {"title": "", "topic": "online", "youtube_id": "dQw4w9WgXcQ"}, format="json")
        self.assertIn("title", response.json())

    def test_only_staff(self):
        self.client.force_authenticate(self.tutor)
        self.assertEqual(self.client.get(reverse("staff-videos")).status_code, 403)
        self.assertEqual(self.client.post(reverse("staff-videos"), {"title": "x", "youtube_id": "dQw4w9WgXcQ"}, format="json").status_code, 403)
