"""The installable-app files must reach phones with the right type and never go stale."""
import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from config.settings import _whitenoise_html_headers

PUBLIC = Path(settings.BASE_DIR).parent / "frontend" / "public"


class InstallableAppTests(SimpleTestCase):
    def test_manifest_has_its_proper_file_type(self):
        self.assertEqual(settings.WHITENOISE_MIMETYPES[".webmanifest"], "application/manifest+json")

    def test_service_worker_and_manifest_are_never_cached(self):
        for url in ("/sw.js", "/manifest.webmanifest"):
            headers = {}
            _whitenoise_html_headers(headers, f"/dist{url}", url)
            self.assertEqual(headers.get("Cache-Control"), "no-cache", url)

    def test_offline_page_gets_the_security_policy(self):
        headers = {}
        _whitenoise_html_headers(headers, "/dist/offline.html", "/offline.html")
        self.assertEqual(headers["Content-Security-Policy"], settings.CONTENT_SECURITY_POLICY)

    def test_manifest_opens_full_screen_and_its_icons_exist(self):
        manifest = json.loads((PUBLIC / "manifest.webmanifest").read_text())
        self.assertEqual(manifest["display"], "standalone")  # no browser address bar
        self.assertEqual(manifest["start_url"], "/")
        purposes = {icon["purpose"] for icon in manifest["icons"]}
        self.assertEqual(purposes, {"any", "maskable"})
        for icon in manifest["icons"]:
            self.assertTrue((PUBLIC / icon["src"].lstrip("/")).is_file(), icon["src"])

    def test_service_worker_never_touches_api_or_form_posts(self):
        sw = (PUBLIC / "sw.js").read_text()
        self.assertIn("request.method !== 'GET'", sw)
        self.assertNotIn("/api", sw)  # API answers always come live from the server
