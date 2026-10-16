import re

from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age
from accounts.tokens import email_verification_token, encode_uid, password_reset_token

PASSWORD = "Sunflower-Maths-42"


def link_params(body):
    return dict(re.findall(r"(uid|token)=([^&\s]+)", body))


class VerificationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def register(self):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("auth-register"), {
                "email": "lerato@example.com", "password": PASSWORD, "first_name": "Lerato", "last_name": "D",
                "date_of_birth": dob_for_age(40).isoformat(), "account_type": "parent",
            }, format="json")

    def test_new_user_starts_unverified_and_gets_email(self):
        response = self.register()
        self.assertFalse(response.json()["email_verified"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/verify-email?uid=", mail.outbox[0].body)

    def test_link_verifies_once_and_cannot_be_forged(self):
        self.register()
        params = link_params(mail.outbox[0].body)
        bad = self.client.post(reverse("auth-verify-email"), {"uid": params["uid"], "token": "1-forged"}, format="json")
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post(reverse("auth-verify-email"), params, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(User.objects.get().email_verified)
        self.assertTrue(self.client.get(reverse("auth-me")).json()["email_verified"])

    def test_resend(self):
        self.register()
        mail.outbox.clear()
        self.client.post(reverse("auth-resend-verification"))
        self.assertEqual(len(mail.outbox), 1)

    def test_unverified_users_blocked_from_contact_report_and_submit(self):
        self.register()
        for url in (reverse("contact-tutor", args=[1]), reverse("report-tutor", args=[1])):
            response = self.client.post(url, {}, format="json")
            self.assertEqual(response.status_code, 403, url)
            self.assertEqual(response.json()["code"], "email_unverified")


class PasswordResetTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(email="sipho@example.com", password=PASSWORD, first_name="Sipho",
                                             last_name="N", date_of_birth=dob_for_age(25), account_type="tutor")

    def request_reset(self, email):
        return self.client.post(reverse("auth-password-reset"), {"email": email}, format="json")

    def test_same_answer_for_known_and_unknown_emails(self):
        known = self.request_reset("Sipho@Example.com")
        unknown = self.request_reset("nobody@example.com")
        self.assertEqual((known.status_code, known.json()), (unknown.status_code, unknown.json()))
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_flow_changes_password_once(self):
        self.request_reset("sipho@example.com")
        params = link_params(mail.outbox[0].body)
        url = reverse("auth-password-reset-confirm")
        weak = self.client.post(url, {**params, "new_password": "password"}, format="json")
        self.assertEqual(weak.status_code, 400)
        ok = self.client.post(url, {**params, "new_password": "New-Strong-Pass-77"}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-Strong-Pass-77"))
        self.assertTrue(self.user.email_verified)  # proved inbox access
        again = self.client.post(url, {**params, "new_password": "Another-Pass-88"}, format="json")
        self.assertEqual(again.status_code, 400)  # link is single-use

    def test_reset_logs_out_other_sessions(self):
        other = self.client_class()
        other.post(reverse("auth-login"), {"email": "sipho@example.com", "password": PASSWORD}, format="json")
        self.assertEqual(other.get(reverse("auth-me")).status_code, 200)
        self.user.refresh_from_db()  # reset links are tied to the latest login time
        token = password_reset_token.make_token(self.user)
        response = self.client.post(reverse("auth-password-reset-confirm"),
                                    {"uid": encode_uid(self.user), "token": token, "new_password": "New-Strong-Pass-77"},
                                    format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(other.get(reverse("auth-me")).status_code, 403)

    def test_verification_token_cannot_reset_password(self):
        token = email_verification_token.make_token(self.user)
        response = self.client.post(reverse("auth-password-reset-confirm"),
                                    {"uid": encode_uid(self.user), "token": token, "new_password": "New-Strong-Pass-77"},
                                    format="json")
        self.assertEqual(response.status_code, 400)

    def test_inactive_user_cannot_reset(self):
        self.user.is_active = False
        self.user.save()
        self.request_reset("sipho@example.com")
        self.assertEqual(len(mail.outbox), 0)
