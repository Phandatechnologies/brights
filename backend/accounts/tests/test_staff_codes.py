"""Two-step login for staff: password, then a 6-digit code emailed to them."""

import re
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import StaffLoginCode, User
from accounts.tests.helpers import dob_for_age

PASSWORD = "Sunflower-Maths-42"


class StaffCodeTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_superuser(email="busi@example.com", password=PASSWORD, first_name="Busi",
                                                   last_name="Staff", date_of_birth=dob_for_age(30))

    def password_step(self, email="busi@example.com", password=PASSWORD):
        return self.client.post(reverse("auth-login"), {"email": email, "password": password}, format="json")

    def emailed_code(self):
        return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

    def code_step(self, challenge, code):
        return self.client.post(reverse("auth-login-code"), {"challenge": challenge, "code": code}, format="json")

    def me(self):
        return self.client.get(reverse("auth-me"))

    def test_password_then_code_logs_in(self):
        response = self.password_step()
        self.assertEqual(response.json().keys(), {"code_required", "challenge"})  # no user details yet
        self.assertEqual(self.me().status_code, 403)
        self.assertEqual(mail.outbox[-1].to, ["busi@example.com"])
        code = self.emailed_code()
        self.assertNotIn(code, str(StaffLoginCode.objects.values_list("code_hash", flat=True)))  # only a hash is stored
        response = self.code_step(response.json()["challenge"], code)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_staff"])
        self.assertEqual(self.me().json()["email"], "busi@example.com")

    def test_code_is_single_use(self):
        challenge = self.password_step().json()["challenge"]
        code = self.emailed_code()
        self.assertEqual(self.code_step(challenge, code).status_code, 200)
        self.client.logout()
        self.assertEqual(self.code_step(challenge, code).status_code, 400)

    def test_wrong_password_sends_no_code(self):
        self.assertEqual(self.password_step(password="wrong").status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_five_wrong_codes_cancel_it(self):
        challenge = self.password_step().json()["challenge"]
        right = self.emailed_code()
        wrong = "000000" if right != "000000" else "111111"
        messages = [self.code_step(challenge, wrong).json()["detail"] for _ in range(5)]
        self.assertIn("4 tries left", messages[0])
        self.assertIn("Too many wrong codes", messages[-1])
        self.assertEqual(self.code_step(challenge, right).status_code, 400)  # even the right one is now dead
        self.assertEqual(self.me().status_code, 403)

    def test_code_expires_after_10_minutes(self):
        challenge = self.password_step().json()["challenge"]
        code = self.emailed_code()
        StaffLoginCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.code_step(challenge, code)
        self.assertIn("expired", response.json()["detail"])

    def test_new_code_cancels_old_one(self):
        first = self.password_step().json()["challenge"]
        first_code = self.emailed_code()
        second = self.password_step().json()["challenge"]
        self.assertEqual(self.code_step(first, first_code).status_code, 400)
        self.assertEqual(self.code_step(second, self.emailed_code()).status_code, 200)

    def test_code_from_one_login_cannot_be_used_with_another(self):
        other = User.objects.create_superuser(email="sam@example.com", password=PASSWORD, first_name="Sam",
                                              last_name="Staff", date_of_birth=dob_for_age(30))
        mine = self.password_step().json()["challenge"]
        my_code = self.emailed_code()
        theirs = self.password_step(email=other.email).json()["challenge"]
        if my_code != self.emailed_code():
            self.assertEqual(self.code_step(theirs, my_code).status_code, 400)
        self.assertEqual(self.code_step(mine, my_code).json()["email"], "busi@example.com")

    def test_blocked_or_demoted_staff_cannot_finish(self):
        challenge = self.password_step().json()["challenge"]
        code = self.emailed_code()
        User.objects.filter(pk=self.staff.pk).update(is_staff=False)
        self.assertEqual(self.code_step(challenge, code).status_code, 400)
        self.assertEqual(self.me().status_code, 403)

    def test_email_failure_is_explained_and_does_not_log_in(self):
        with mock.patch("accounts.views.send_staff_login_code", return_value=False):
            response = self.password_step()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.me().status_code, 403)

    def test_learners_and_tutors_log_in_as_before(self):
        User.objects.create_user(email="lerato@example.com", password=PASSWORD, first_name="L", last_name="M",
                                 date_of_birth=dob_for_age(20), account_type="tutor")
        response = self.password_step(email="lerato@example.com")
        self.assertEqual(response.json()["email"], "lerato@example.com")
        self.assertEqual(len(mail.outbox), 0)


class AdminLoginTests(APITestCase):
    def test_admin_login_page_sends_staff_to_the_two_step_login(self):
        admin_login = f"/{settings.ADMIN_URL}login/"
        response = self.client.get(admin_login, {"next": f"/{settings.ADMIN_URL}tutors/"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"/login?next=%2F{settings.ADMIN_URL.replace('/', '%2F')}tutors%2F")

    def test_password_cannot_be_posted_to_the_admin(self):
        User.objects.create_superuser(email="busi@example.com", password=PASSWORD, first_name="B", last_name="S",
                                      date_of_birth=dob_for_age(30))
        self.client.post(f"/{settings.ADMIN_URL}login/", {"username": "busi@example.com", "password": PASSWORD})
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 403)
        response = self.client.get(f"/{settings.ADMIN_URL}")
        self.assertEqual(response.status_code, 302)  # still not signed in

    def test_outside_next_links_are_ignored(self):
        response = self.client.get(f"/{settings.ADMIN_URL}login/", {"next": "https://evil.example.com/"})
        self.assertNotIn("evil", response["Location"])
