"""
Remove the test accounts made while building and testing Brights.

    python manage.py remove_test_accounts            # only LISTS what would be removed
    python manage.py remove_test_accounts --delete   # removes them, after you type a confirmation

Staff and admin accounts are always kept. Everything belonging to the removed accounts goes
too: tutor applications and their decision history, uploaded documents and photos (also
deleted from file storage), profiles, contacts and reports. This cannot be undone.

For use before launch only: it refuses to remove more than --limit accounts (default 50),
so it can't wipe real users by accident later.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from moderation.models import Report
from profiles.models import TutorProfile
from tutors.models import ApplicationDocument, ApplicationEvent, TutorApplication


class Command(BaseCommand):
    help = "List, then optionally remove, all non-staff accounts (test data from before launch)."

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true", help="Actually remove them (asks you to confirm).")
        parser.add_argument("--keep", action="append", default=[], metavar="EMAIL",
                            help="An extra account to keep (repeat for more).")
        parser.add_argument("--limit", type=int, default=50, help="Refuse if more accounts than this would go.")

    def handle(self, *args, delete, keep, limit, **options):
        User = get_user_model()
        keep = {e.strip().lower() for e in keep}
        targets = (User.objects.filter(is_staff=False, is_superuser=False)
                   .exclude(email__in=keep).order_by("date_joined"))
        users = list(targets)
        kept = User.objects.exclude(pk__in=[u.pk for u in users]).order_by("email")

        self.stdout.write(f"Accounts kept ({kept.count()}):")
        for u in kept:
            self.stdout.write(f"  KEEP    {u.email}  ({'admin' if u.is_superuser else 'staff' if u.is_staff else 'kept'})")
        self.stdout.write(f"\nAccounts to remove ({len(users)}):")
        for u in users:
            self.stdout.write(f"  REMOVE  {u.email}  ({u.account_type}, joined {u.date_joined:%Y-%m-%d})")

        if not users:
            self.stdout.write(self.style.SUCCESS("\nNothing to remove."))
            return
        if len(users) > limit:
            raise CommandError(f"{len(users)} accounts is more than the limit of {limit}. "
                               "This tool is for clearing test data before launch; if you're sure, pass --limit.")

        profiles = TutorProfile.objects.filter(user__in=users)
        applications = TutorApplication.objects.filter(user__in=users)
        documents = list(ApplicationDocument.objects.filter(application__in=applications))
        photos = [p.photo for p in profiles if p.photo]
        reports = Report.objects.filter(Q(tutor__in=profiles) | Q(reporter__in=users))
        self.stdout.write(f"\nAlso removed: {applications.count()} tutor application(s), {len(documents)} document(s), "
                          f"{len(photos)} photo(s), {reports.count()} report(s), and their contacts and history.")

        if not delete:
            self.stdout.write(self.style.WARNING("\nNothing was changed. To remove these, run again with --delete."))
            return

        expected = f"DELETE {len(users)}"
        answer = input(f"\nThis cannot be undone. Type {expected} to confirm: ").strip()
        if answer != expected:
            raise CommandError("Not confirmed. Nothing was changed.")

        files = [d.file for d in documents] + photos
        with transaction.atomic():
            reports.delete()  # test reports; normally reports can't be deleted
            ApplicationEvent.objects.filter(application__in=applications).delete()  # protected decision history
            targets.delete()  # cascades: applications, documents, profiles, contacts, view counts, acknowledgements
            # Remove the stored files only once the database change is saved.
            transaction.on_commit(lambda: self._delete_files(files))
        self.stdout.write(self.style.SUCCESS(f"\nRemoved {len(users)} account(s)."))

    def _delete_files(self, files):
        failed = 0
        for f in files:
            try:
                f.storage.delete(f.name)
            except Exception:
                failed += 1
        if failed:
            self.stdout.write(self.style.WARNING(f"{failed} stored file(s) couldn't be deleted; remove them in storage."))
