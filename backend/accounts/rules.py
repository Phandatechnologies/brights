"""
Sign-up business rules for Brights, kept separate from views and serializers
so they are easy to read, change and test.

Rules (agreed in Phase 3):
1. Tutors must be at least 18.
2. Parents/guardians must be at least 18.
3. Learners must be at least 12.
4. Learners under 18 must confirm guardian consent and give the guardian's full name.
"""

from datetime import date

ADULT_AGE = 18
MIN_LEARNER_AGE = 12
MAX_PLAUSIBLE_AGE = 100


class AccountType:
    LEARNER = "learner"
    PARENT = "parent"
    TUTOR = "tutor"

    CHOICES = [
        (LEARNER, "Learner"),
        (PARENT, "Parent or guardian"),
        (TUTOR, "Tutor"),
    ]


def age_on(date_of_birth: date, today: date) -> int:
    """Age in whole years on a given day (birthday not yet reached = one year less)."""
    had_birthday = (today.month, today.day) >= (date_of_birth.month, date_of_birth.day)
    return today.year - date_of_birth.year - (0 if had_birthday else 1)


def registration_errors(*, account_type, date_of_birth, guardian_consent, guardian_name, today):
    """
    Return a dict of {field: message} for every rule the sign-up breaks.
    An empty dict means the sign-up is allowed.
    """
    errors = {}

    if date_of_birth > today:
        return {"date_of_birth": "Date of birth cannot be in the future."}

    age = age_on(date_of_birth, today)
    if age > MAX_PLAUSIBLE_AGE:
        return {"date_of_birth": "Please check your date of birth."}

    if account_type == AccountType.TUTOR and age < ADULT_AGE:
        errors["account_type"] = "You must be at least 18 to register as a tutor."

    elif account_type == AccountType.PARENT and age < ADULT_AGE:
        errors["account_type"] = "You must be at least 18 to register as a parent or guardian."

    elif account_type == AccountType.LEARNER:
        if age < MIN_LEARNER_AGE:
            errors["date_of_birth"] = f"Learners must be at least {MIN_LEARNER_AGE} years old."
        elif age < ADULT_AGE:
            if not guardian_consent:
                errors["guardian_consent"] = "A parent or guardian must agree before you can register."
            if not (guardian_name or "").strip():
                errors["guardian_name"] = "Please enter your parent or guardian's full name."

    return errors
