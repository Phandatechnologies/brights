"""Email problems must never freeze or crash what the person is doing."""

import socket
import threading
import time
from unittest.mock import patch

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.test_api import payload


def broken_send_mail(*args, **kwargs):
    raise ConnectionRefusedError("mail server unreachable")


class SilentServer:
    """Accepts connections and never answers, like a blocked or dead mail server."""

    def __enter__(self):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        self.clients = []
        self._stop = False
        threading.Thread(target=self._accept, daemon=True).start()
        return self

    def _accept(self):
        self.sock.settimeout(0.2)
        while not self._stop:
            try:
                self.clients.append(self.sock.accept()[0])
            except OSError:
                pass

    def __exit__(self, *exc):
        self._stop = True
        for c in self.clients:
            c.close()
        self.sock.close()


class EmailFailureTests(APITestCase):
    def setUp(self):
        cache.clear()

    @patch("core.mail.send_mail", side_effect=broken_send_mail)
    def test_sign_up_still_works_when_email_fails(self, _):
        with self.assertLogs("brights.email", level="ERROR") as logs, self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("auth-register"), payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="lerato@example.com").exists())
        self.assertNotIn("lerato@example.com", "\n".join(logs.output))  # no addresses in logs

    @patch("core.mail.send_mail", side_effect=broken_send_mail)
    def test_resend_says_honestly_that_it_failed(self, _):
        user = User.objects.create_user(email="u@example.com", password="Sunflower-Maths-42", first_name="U",
                                        last_name="V", date_of_birth="1990-01-01", account_type="parent")
        self.client.force_authenticate(user)
        with self.assertLogs("brights.email", level="ERROR"):
            response = self.client.post(reverse("auth-resend-verification"))
        self.assertEqual(response.status_code, 503)

    @patch("core.mail.send_mail", side_effect=broken_send_mail)
    def test_password_reset_answer_is_unchanged_when_email_fails(self, _):
        User.objects.create_user(email="u@example.com", password="Sunflower-Maths-42", first_name="U",
                                 last_name="V", date_of_birth="1990-01-01", account_type="parent")
        with self.assertLogs("brights.email", level="ERROR"):
            response = self.client.post(reverse("auth-password-reset"), {"email": "u@example.com"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_silent_mail_server_cannot_freeze_sign_up(self):
        """What happened on Render: the mail port was blocked and sign-up hung until the server killed it."""
        with SilentServer() as server, override_settings(
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="127.0.0.1",
            EMAIL_PORT=server.port, EMAIL_USE_TLS=True, EMAIL_TIMEOUT=2,
        ), self.assertLogs("brights.email", level="ERROR"), self.captureOnCommitCallbacks(execute=True):
            started = time.monotonic()
            response = self.client.post(reverse("auth-register"), payload(email="slow@example.com"), format="json")
            elapsed = time.monotonic() - started
        self.assertEqual(response.status_code, 201)
        self.assertLess(elapsed, 10)
