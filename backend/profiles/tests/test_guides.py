from django.conf import settings
from django.contrib.admin.sites import site
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from profiles.models import GuideVideo
from profiles.rules import youtube_video_id

VID = "dQw4w9WgXcQ"


class YoutubeLinkTests(SimpleTestCase):
    def test_accepts_common_youtube_links(self):
        for link in (VID, f"https://www.youtube.com/watch?v={VID}", f"https://youtube.com/watch?v={VID}&t=42s",
                     f"https://youtu.be/{VID}", f"https://youtu.be/{VID}?si=abc", f"youtu.be/{VID}",
                     f"https://m.youtube.com/watch?v={VID}", f"https://www.youtube.com/shorts/{VID}",
                     f"https://www.youtube.com/embed/{VID}", f"https://www.youtube.com/live/{VID}"):
            self.assertEqual(youtube_video_id(link), VID, link)

    def test_rejects_everything_else(self):
        for link in ("", "hello", "https://vimeo.com/12345678", f"https://evil.example/watch?v={VID}",
                     f"https://youtube.com.evil.example/watch?v={VID}", "https://youtube.com/watch?v=short",
                     "https://www.youtube.com/@brights", "javascript:alert(1)"):
            self.assertIsNone(youtube_video_id(link), link)

    def test_policy_allows_only_the_youtube_player_and_thumbnails(self):
        csp = settings.CONTENT_SECURITY_POLICY
        self.assertIn("frame-src https://www.youtube-nocookie.com", csp)
        self.assertIn("img-src 'self' data: https://i.ytimg.com", csp)
        self.assertIn("script-src 'self';", csp + ";")


def person(email, account_type):
    return User.objects.create_user(email=email, password="Sunflower-Maths-42", first_name="A", last_name="B",
                                    date_of_birth=dob_for_age(30), account_type=account_type,
                                    email_verified_at=timezone.now())


class GuideVideoTests(APITestCase):
    url = reverse("tutor-guides")

    def test_admin_form_turns_a_pasted_link_into_the_id(self):
        form_class = site._registry[GuideVideo].get_form(request=None)
        form = form_class(data={"title": "Your first online lesson", "topic": "online",
                                "youtube_id": f"https://youtu.be/{VID}?si=x", "order": 1, "is_published": True})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().youtube_id, VID)
        bad = form_class(data={"title": "x", "topic": "online", "youtube_id": "https://vimeo.com/1", "order": 0})
        self.assertFalse(bad.is_valid())
        self.assertIn("youtube_id", bad.errors)

    @override_settings(YOUTUBE_CHANNEL_URL="https://www.youtube.com/@brights")
    def test_tutors_see_published_videos_in_order(self):
        GuideVideo.objects.create(title="Online", topic="online", youtube_id=VID, order=2, is_published=True)
        GuideVideo.objects.create(title="Start here", topic="getting_started", youtube_id=VID, order=1, is_published=True)
        GuideVideo.objects.create(title="Draft", topic="in_person", youtube_id=VID, order=0, is_published=False)
        self.client.force_authenticate(person("t@example.com", "tutor"))
        body = self.client.get(self.url).json()
        self.assertEqual([v["title"] for v in body["videos"]], ["Start here", "Online"])
        self.assertEqual(body["videos"][0]["youtube_id"], VID)
        self.assertEqual(body["channel_url"], "https://www.youtube.com/@brights")

    def test_only_tutors(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_authenticate(person("p@example.com", "parent"))
        self.assertEqual(self.client.get(self.url).status_code, 403)
