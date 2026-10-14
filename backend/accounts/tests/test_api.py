from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from accounts.tests.helpers import dob_for_age

PASSWORD = "Sunflower-Maths-42"


def payload(**overrides):
    data = {
        "email": "lerato@example.com",
        "password": PASSWORD,
        "first_name": "Lerato",
        "last_name": "Dlamini",
        "date_of_birth": dob_for_age(30).isoformat(),
        "account_type": "parent",
    }
    data.update(overrides)
    return data


class AuthTestCase(APITestCase):
    def setUp(self):
        cache.clear()  # reset rate limiting between tests


class RegisterTests(AuthTestCase):
    url = reverse("auth-register")

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(self.url, payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["account_type"], "parent")
        me = self.client.get(reverse("auth-me"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], "lerato@example.com")

    def test_password_is_hashed_and_never_returned(self):
        response = self.client.post(self.url, payload(), format="json")
        self.assertNotIn("password", response.json())
        self.assertNotIn(PASSWORD, response.content.decode())
        user = User.objects.get(email="lerato@example.com")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_email_is_case_insensitive(self):
        self.client.post(self.url, payload(email="Lerato@Example.com"), format="json")
        self.assertTrue(User.objects.filter(email="lerato@example.com").exists())
        self.client.logout()
        response = self.client.post(self.url, payload(email="LERATO@example.COM"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_cannot_make_yourself_admin(self):
        response = self.client.post(
            self.url, payload(is_staff=True, is_superuser=True), format="json"
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="lerato@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_cannot_register_as_admin_account_type(self):
        response = self.client.post(self.url, payload(account_type="admin"), format="json")
        self.assertEqual(response.status_code, 400)

    def test_weak_password_rejected(self):
        response = self.client.post(self.url, payload(password="12345678"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())

    def test_underage_tutor_rejected(self):
        response = self.client.post(
            self.url, payload(account_type="tutor", date_of_birth=dob_for_age(17).isoformat()),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("account_type", response.json())
        self.assertFalse(User.objects.exists())

    def test_minor_learner_without_consent_rejected(self):
        response = self.client.post(
            self.url, payload(account_type="learner", date_of_birth=dob_for_age(15).isoformat()),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("guardian_consent", response.json())

    def test_minor_learner_with_consent_records_it(self):
        response = self.client.post(
            self.url,
            payload(account_type="learner", date_of_birth=dob_for_age(15).isoformat(),
                    guardian_consent=True, guardian_name="  Thandi Dlamini "),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["is_minor"])
        user = User.objects.get(email="lerato@example.com")
        self.assertEqual(user.guardian_name, "Thandi Dlamini")
        self.assertIsNotNone(user.guardian_consent_given_at)

    def test_guardian_details_discarded_for_adults(self):
        self.client.post(
            self.url, payload(guardian_consent=True, guardian_name="Someone Else"), format="json"
        )
        user = User.objects.get(email="lerato@example.com")
        self.assertEqual(user.guardian_name, "")
        self.assertIsNone(user.guardian_consent_given_at)


class LoginLogoutTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            email="sipho@example.com", password=PASSWORD, first_name="Sipho",
            last_name="Nkosi", date_of_birth=dob_for_age(20), account_type="tutor",
        )

    def login(self, email="sipho@example.com", password=PASSWORD):
        return self.client.post(
            reverse("auth-login"), {"email": email, "password": password}, format="json"
        )

    def test_login_success_with_any_email_case(self):
        response = self.login(email="Sipho@Example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "sipho@example.com")

    def test_wrong_password_and_unknown_email_give_same_error(self):
        wrong = self.login(password="not-the-password")
        unknown = self.login(email="nobody@example.com")
        self.assertEqual(wrong.status_code, 400)
        self.assertEqual(wrong.json(), unknown.json())

    def test_suspended_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, 400)

    def test_me_requires_login(self):
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 403)

    def test_logout_ends_session(self):
        self.login()
        self.assertEqual(self.client.post(reverse("auth-logout")).status_code, 204)
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 403)

    def test_login_is_rate_limited(self):
        statuses = [self.login(password="wrong").status_code for _ in range(11)]
        self.assertEqual(statuses[-1], 429)


class CsrfTests(AuthTestCase):
    """Uses a client that enforces CSRF like a real browser would."""

    def setUp(self):
        super().setUp()
        self.client = APIClient(enforce_csrf_checks=True)

    def test_login_without_csrf_token_is_rejected(self):
        response = self.client.post(
            reverse("auth-login"), {"email": "a@example.com", "password": "x"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_register_with_csrf_token_succeeds(self):
        self.client.get(reverse("auth-csrf"))
        token = self.client.cookies["csrftoken"].value
        response = self.client.post(
            reverse("auth-register"), payload(), format="json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(response.status_code, 201)
