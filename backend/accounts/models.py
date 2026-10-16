from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from .rules import ADULT_AGE, AccountType, age_on


class UserManager(BaseUserManager):
    """Creates users with email as the login instead of a username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # stores a salted hash, never the raw password
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    A Brights account. Email is the login.

    account_type is chosen at sign-up and never changes through the API.
    Administrators are identified ONLY by is_staff, which is never writable
    through any API endpoint (set it with createsuperuser or the Django admin).
    Platform staff may have an empty account_type.
    """

    email = models.EmailField("email address", unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    account_type = models.CharField(max_length=20, choices=AccountType.CHOICES, blank=True)

    # Guardian consent, recorded only for learners under 18 at sign-up.
    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_consent_given_at = models.DateTimeField(null=True, blank=True)

    # Set when the user clicks the link in their verification email (or resets their password).
    email_verified_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)  # False = suspended / cannot log in
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "date_of_birth"]

    class Meta:
        ordering = ["-date_joined"]

    def save(self, *args, **kwargs):
        # Store emails in lowercase so "Thabo@Mail.com" and "thabo@mail.com" are one account.
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def age(self) -> int:
        return age_on(self.date_of_birth, timezone.localdate())

    @property
    def is_minor(self) -> bool:
        # Calculated every time, so it can never go out of date.
        return self.age < ADULT_AGE

    def __str__(self):
        return self.email
