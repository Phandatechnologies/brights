from django.contrib.auth import password_validation
from django.utils import timezone
from rest_framework import serializers

from .models import User
from .rules import AccountType, age_on, ADULT_AGE, registration_errors


class UserSerializer(serializers.ModelSerializer):
    """What the API reveals about the logged-in user. Read-only."""

    is_minor = serializers.BooleanField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "date_of_birth", "account_type", "is_minor", "email_verified"]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """
    Sign-up input. Only the fields listed here are accepted; anything else in the
    request (e.g. is_staff, is_superuser) is silently ignored and can never be set.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    date_of_birth = serializers.DateField()
    account_type = serializers.ChoiceField(choices=AccountType.CHOICES)
    guardian_consent = serializers.BooleanField(required=False, default=False)
    guardian_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        errors = registration_errors(
            account_type=attrs["account_type"],
            date_of_birth=attrs["date_of_birth"],
            guardian_consent=attrs["guardian_consent"],
            guardian_name=attrs["guardian_name"],
            today=timezone.localdate(),
        )
        if errors:
            raise serializers.ValidationError(errors)

        # Django's password rules (length, common passwords, too similar to name/email, all-numeric).
        candidate = User(
            email=attrs["email"], first_name=attrs["first_name"], last_name=attrs["last_name"]
        )
        try:
            password_validation.validate_password(attrs["password"], user=candidate)
        except Exception as exc:  # django.core.exceptions.ValidationError
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        consent = validated_data.pop("guardian_consent")
        guardian_name = validated_data.pop("guardian_name").strip()
        password = validated_data.pop("password")

        is_minor_learner = (
            validated_data["account_type"] == AccountType.LEARNER
            and age_on(validated_data["date_of_birth"], timezone.localdate()) < ADULT_AGE
        )
        if is_minor_learner and consent:
            validated_data["guardian_name"] = guardian_name
            validated_data["guardian_consent_given_at"] = timezone.now()
        # Data minimisation: guardian details are discarded for everyone else.

        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class TokenSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(TokenSerializer):
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
