from datetime import date

from django.test import SimpleTestCase

from accounts.rules import AccountType, age_on, registration_errors
from accounts.tests.helpers import dob_for_age

TODAY = date(2026, 10, 14)


def errors_for(account_type, age, consent=False, guardian_name=""):
    return registration_errors(
        account_type=account_type,
        date_of_birth=dob_for_age(age, TODAY),
        guardian_consent=consent,
        guardian_name=guardian_name,
        today=TODAY,
    )


class AgeTests(SimpleTestCase):
    def test_birthday_not_yet_reached_this_year(self):
        self.assertEqual(age_on(date(2008, 10, 15), TODAY), 17)

    def test_birthday_today(self):
        self.assertEqual(age_on(date(2008, 10, 14), TODAY), 18)


class TutorRuleTests(SimpleTestCase):
    def test_17_year_old_cannot_register_as_tutor(self):
        self.assertIn("account_type", errors_for(AccountType.TUTOR, 17))

    def test_18_year_old_can_register_as_tutor(self):
        self.assertEqual(errors_for(AccountType.TUTOR, 18), {})


class ParentRuleTests(SimpleTestCase):
    def test_17_year_old_cannot_register_as_parent(self):
        self.assertIn("account_type", errors_for(AccountType.PARENT, 17))

    def test_adult_can_register_as_parent(self):
        self.assertEqual(errors_for(AccountType.PARENT, 40), {})


class LearnerRuleTests(SimpleTestCase):
    def test_11_year_old_learner_rejected(self):
        self.assertIn("date_of_birth", errors_for(AccountType.LEARNER, 11, True, "Thandi Mokoena"))

    def test_minor_learner_needs_consent_and_guardian_name(self):
        errors = errors_for(AccountType.LEARNER, 15)
        self.assertIn("guardian_consent", errors)
        self.assertIn("guardian_name", errors)

    def test_minor_learner_with_consent_allowed(self):
        self.assertEqual(errors_for(AccountType.LEARNER, 12, True, "Thandi Mokoena"), {})

    def test_whitespace_guardian_name_rejected(self):
        self.assertIn("guardian_name", errors_for(AccountType.LEARNER, 15, True, "   "))

    def test_adult_learner_needs_no_consent(self):
        self.assertEqual(errors_for(AccountType.LEARNER, 18), {})


class DateSanityTests(SimpleTestCase):
    def test_future_date_of_birth_rejected(self):
        errors = registration_errors(
            account_type=AccountType.PARENT, date_of_birth=date(2030, 1, 1),
            guardian_consent=False, guardian_name="", today=TODAY,
        )
        self.assertIn("date_of_birth", errors)
