from datetime import date, timedelta

from django.utils import timezone


def dob_for_age(age: int, today: date | None = None) -> date:
    """A date of birth that makes someone exactly `age` today (birthday was yesterday)."""
    today = today or timezone.localdate()
    try:
        birthday = today.replace(year=today.year - age)
    except ValueError:  # 29 February in a non-leap year
        birthday = today.replace(year=today.year - age, day=28)
    return birthday - timedelta(days=1)
