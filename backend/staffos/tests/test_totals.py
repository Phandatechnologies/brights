"""The signed, totals-only address Phanda Staff OS reads. Brights has learners under 18: nothing about any person may
ever leave, and only whole-platform weekly totals are sent."""

import time
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from contact.models import ContactEvent
from moderation.models import Report
from profiles.models import ProfileViewDay, TutorProfile
from staffos import signing
from tutors.models import ApplicationEvent, TutorApplication

SECRET = "test-only-secret"
URL = "/api/internal/staff-os/metrics/"
MON, SUN = date(2026, 9, 7), date(2026, 9, 13)   # a finished Monday–Sunday week
User = get_user_model()


def at(d: date, hour=12):
    return timezone.make_aware(datetime(d.year, d.month, d.day, hour), timezone.get_current_timezone())


def person(email, kind, joined, staff=False, active=True, first="Lerato", last="Mokoena"):
    u = User.objects.create_user(email=email, password="Sekhukhune#2026", first_name=first, last_name=last,
                                 date_of_birth=date(2010, 3, 4) if kind == "learner" else date(1995, 5, 6),
                                 account_type=kind, is_staff=staff, is_active=active,
                                 guardian_name="Thandi Mokoena" if kind == "learner" else "")
    User.objects.filter(pk=u.pk).update(date_joined=at(joined))
    return u


def event(app, to_status, when, from_status="draft"):
    e = ApplicationEvent.objects.create(application=app, action=to_status, from_status=from_status, to_status=to_status)
    ApplicationEvent.objects.filter(pk=e.pk).update(created_at=at(when))


@override_settings(STAFF_OS_METRICS_SECRET=SECRET)
class StaffOsTotalsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Learners and parents
        cls.l1 = person("lindiwe@learner.test", "learner", MON - timedelta(days=30), first="Lindiwe")
        cls.l2 = person("sipho@learner.test", "learner", MON + timedelta(days=2), first="Sipho")
        person("late@learner.test", "learner", SUN + timedelta(days=1))                 # after the week
        person("gone@learner.test", "learner", MON - timedelta(days=60), active=False)   # suspended
        cls.p1 = person("parent@parent.test", "parent", MON - timedelta(days=10), first="Nomsa")
        person("admin@brights.test", "", MON - timedelta(days=90), staff=True)           # staff: left out
        # Tutors: approved before the week; approved during the week then suspended after it; pending only
        t1 = person("tutor1@tutor.test", "tutor", MON - timedelta(days=40), first="Kabelo")
        t2 = person("tutor2@tutor.test", "tutor", MON - timedelta(days=20), first="Ayanda")
        t3 = person("tutor3@tutor.test", "tutor", MON - timedelta(days=5), first="Zanele")
        a1 = TutorApplication.objects.create(user=t1, pathway="academic", status="approved")
        a2 = TutorApplication.objects.create(user=t2, pathway="academic", status="suspended")
        a3 = TutorApplication.objects.create(user=t3, pathway="academic", status="pending")
        event(a1, "pending", MON - timedelta(days=35)); event(a1, "approved", MON - timedelta(days=30), "pending")
        event(a2, "pending", MON + timedelta(days=1)); event(a2, "approved", MON + timedelta(days=3), "pending")
        event(a2, "suspended", SUN + timedelta(days=4), "approved")                     # later: still counted then
        event(a3, "pending", MON + timedelta(days=2))
        cls.prof1 = TutorProfile.objects.create(user=t1, teaches_online=True, whatsapp_number="+27820000001")
        prof2 = TutorProfile.objects.create(user=t2, teaches_online=True, whatsapp_number="+27820000002")
        # Contacts: Lindiwe (also contacted last week) twice, the parent once, one last week
        for who, when in ((cls.l1, MON - timedelta(days=3)), (cls.l1, MON + timedelta(days=1)),
                          (cls.l1, MON + timedelta(days=4)), (cls.p1, MON + timedelta(days=5))):
            c = ContactEvent.objects.create(requester=who, tutor=cls.prof1, requester_was_minor=who == cls.l1)
            ContactEvent.objects.filter(pk=c.pk).update(created_at=at(when))
        # Profile views
        ProfileViewDay.objects.create(profile=cls.prof1, date=MON, count=5)
        ProfileViewDay.objects.create(profile=prof2, date=SUN, count=3)
        ProfileViewDay.objects.create(profile=prof2, date=SUN + timedelta(days=1), count=50)
        # Safety reports: one urgent child-safety report during the week, one before
        for urgent, when in ((True, MON + timedelta(days=2)), (False, MON - timedelta(days=1))):
            r = Report.objects.create(reporter=cls.l1, tutor=prof2, category="child_safety",
                                      description="He asked me to meet alone", is_urgent=urgent, reporter_was_minor=True)
            Report.objects.filter(pk=r.pk).update(created_at=at(when))

    def get(self, start=MON, end=SUN, secret=SECRET, ts=None, tamper=False):
        path = f"{URL}?start={start.isoformat()}&end={end.isoformat()}"
        ts = int(time.time()) if ts is None else ts
        sig = signing.sign(secret, ts, "GET", path)
        if tamper:
            path = path.replace(f"start={start.isoformat()}", f"start={(start - timedelta(days=7)).isoformat()}")
        return self.client.get(path, HTTP_X_STAFF_OS_TIMESTAMP=str(ts), HTTP_X_STAFF_OS_SIGNATURE=sig)

    @override_settings(STAFF_OS_METRICS_SECRET="")
    def test_off_unless_the_secret_is_set(self):
        self.assertEqual(self.get().status_code, 404)

    def test_signature_is_required(self):
        self.assertEqual(self.client.get(f"{URL}?start={MON}&end={SUN}").status_code, 403)
        self.assertEqual(self.get(secret="wrong").status_code, 403)
        self.assertEqual(self.get(ts=int(time.time()) - 301).status_code, 403)
        self.assertEqual(self.get(tamper=True).status_code, 403)
        self.assertEqual(self.client.post(f"{URL}?start={MON}&end={SUN}").status_code, 405)

    def test_dates_are_checked(self):
        self.assertEqual(self.get(start=SUN, end=MON).status_code, 400)
        self.assertEqual(self.get(start=MON - timedelta(days=200)).status_code, 400)
        future = timezone.localdate() + timedelta(days=1)
        self.assertEqual(self.get(start=future, end=future).status_code, 400)

    def test_counts_follow_the_agreed_definitions(self):
        r = self.get()
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual((body["app"], body["schema"], body["start"], body["end"]), ("brights", 1, "2026-09-07", "2026-09-13"))
        m = {k: v["value"] for k, v in body["metrics"].items()}
        self.assertEqual(m["registered-users"], 2)       # learners: Lindiwe, Sipho (not late, not suspended)
        self.assertEqual(m["registered-parents"], 1)
        self.assertEqual(m["verified-tutors"], 2)        # approved at the end of that week (one suspended later)
        self.assertEqual(m["tutor-applications"], 2)     # sent for review during the week
        self.assertEqual(m["contacts-started"], 3)
        self.assertEqual(m["returning-contacts"], 1)     # Lindiwe had also made a contact before
        self.assertEqual(m["profile-views"], 8)
        self.assertEqual(m["safety-reports"], 1)
        self.assertEqual(m["urgent-safety-reports"], 1)
        for key in ("lessons-booked", "weekly-active-users", "retention-4-weeks"):
            self.assertIsNone(m[key])
            self.assertTrue(body["metrics"][key]["reason"])

    def test_a_later_week_sees_the_suspension(self):
        m = self.get(start=MON + timedelta(weeks=1), end=SUN + timedelta(weeks=1)).json()["metrics"]
        self.assertEqual(m["verified-tutors"]["value"], 1)

    def test_nothing_about_any_person_leaves(self):
        with CaptureQueriesContext(connection) as q:
            r = self.get()
        text = r.content.decode().lower()
        for private in ("lindiwe", "sipho", "nomsa", "kabelo", "mokoena", "thandi", "@", "+2782", "2010-03-04",
                        "meet alone", "child_safety", "whatsapp"):
            self.assertNotIn(private, text)
        self.assertEqual(set(r.json()), {"app", "schema", "start", "end", "generated_at", "metrics"})
        for item in r.json()["metrics"].values():
            self.assertTrue(set(item) <= {"value", "reason"})
            self.assertTrue(item["value"] is None or isinstance(item["value"], int))
        self.assertTrue(all(s["sql"].lstrip().upper().startswith("SELECT") for s in q.captured_queries))
        self.assertEqual(r["Cache-Control"], "no-store")

    def test_identical_requests_give_identical_totals(self):
        self.assertEqual(self.get().json()["metrics"], self.get().json()["metrics"])
