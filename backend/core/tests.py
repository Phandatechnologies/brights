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
