from unittest import mock

from django.db import DatabaseError
from django.urls import reverse
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    def test_health_reports_ok_when_database_reachable(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "connected"})

    def test_health_is_public(self):
        # No login: must still be reachable, even though the API default is IsAuthenticated.
        self.client.logout()
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)

    def test_health_reports_degraded_without_leaking_details(self):
        with mock.patch("core.views.connection.cursor", side_effect=DatabaseError("secret host info")):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "degraded", "database": "unavailable"})
        self.assertNotIn("secret", response.content.decode())


# --- Phase 9: production hardening ---------------------------------------------------

import tempfile
from pathlib import Path

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from config.settings import database_from_url
from core.ip import client_ip


class ClientIpTests(SimpleTestCase):
    def request(self, remote="10.0.0.1", forwarded=None):
        meta = {"REMOTE_ADDR": remote}
        if forwarded:
            meta["HTTP_X_FORWARDED_FOR"] = forwarded
        return RequestFactory().get("/", **meta)

    @override_settings(TRUSTED_PROXY_COUNT=0)
    def test_no_proxy_ignores_forwarded_header(self):
        self.assertEqual(client_ip(self.request(forwarded="1.2.3.4")), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_one_proxy_uses_last_forwarded_address(self):
        # An attacker can prepend fake addresses, but the proxy appends the real one last.
        self.assertEqual(client_ip(self.request(forwarded="6.6.6.6, 41.13.0.9")), "41.13.0.9")


class AdminLoginRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_eleventh_attempt_blocked(self):
        url = "/admin/login/"
        statuses = [self.client.post(url, {"username": "x@example.com", "password": "wrong"}).status_code for _ in range(11)]
        self.assertNotIn(429, statuses[:10])
        self.assertEqual(statuses[10], 429)


class DatabaseUrlTests(SimpleTestCase):
    def test_neon_style_url(self):
        db = database_from_url("postgresql://brights_owner:p%40ss@ep-cool-1.eu-central-1.aws.neon.tech/brights?sslmode=require")
        self.assertEqual((db["USER"], db["PASSWORD"], db["HOST"], db["NAME"]), ("brights_owner", "p@ss", "ep-cool-1.eu-central-1.aws.neon.tech", "brights"))
        self.assertEqual(db["OPTIONS"], {"sslmode": "require"})


class SpaTests(TestCase):
    def setUp(self):
        self.dist = Path(tempfile.mkdtemp())
        (self.dist / "index.html").write_text("<!doctype html><div id=root></div>")

    def test_react_pages_served_with_security_headers(self):
        with self.settings(FRONTEND_DIST=self.dist):
            response = self.client.get("/tutors/12")
        self.assertEqual(response.status_code, 200)
        self.assertIn("script-src 'self'", response["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", response["Content-Security-Policy"])

    def test_unknown_api_path_is_not_sent_to_react(self):
        with self.settings(FRONTEND_DIST=self.dist):
            self.assertEqual(self.client.get("/api/does-not-exist/").status_code, 404)

    def test_missing_build_gives_404(self):
        with self.settings(FRONTEND_DIST=self.dist / "missing"):
            self.assertEqual(self.client.get("/dashboard").status_code, 404)


class PrivateStorageSwitchTests(SimpleTestCase):
    def test_local_by_default(self):
        from tutors.uploads import get_private_storage, private_storage
        self.assertIs(get_private_storage(), private_storage)

    @override_settings(PRIVATE_STORAGE_BACKEND="s3", S3_BUCKET="brights-private", S3_ENDPOINT_URL="https://acc.r2.cloudflarestorage.com",
                       S3_ACCESS_KEY_ID="key", S3_SECRET_ACCESS_KEY="secret", S3_REGION="auto")
    def test_s3_is_private(self):
        import tutors.uploads as uploads
        uploads._s3 = None
        storage = uploads.get_private_storage()
        self.assertEqual(storage.bucket_name, "brights-private")
        self.assertIsNone(storage.default_acl)
        self.assertTrue(storage.querystring_auth)
        self.assertEqual(storage.location, "private")
        uploads._s3 = None
