from django.urls import reverse
from rest_framework import serializers

from tutors.rules import Pathway

from .models import Area, TutorProfile
from .queries import approved_subjects
from .rules import MAX_BIO_LENGTH, MAX_HOURLY_RATE, MIN_HOURLY_RATE, PhotoStatus, normalise_sa_mobile


class AreaSerializer(serializers.ModelSerializer):
    province_label = serializers.CharField(source="get_province_display", read_only=True)

    class Meta:
        model = Area
        fields = ["id", "name", "province", "province_label"]


def photo_url(profile):
    if profile.photo and profile.photo_status == PhotoStatus.APPROVED:
        # The URL changes when the photo changes, so browsers never show an old one.
        return reverse("tutor-photo", args=[profile.pk]) + f"?v={int(profile.updated_at.timestamp())}"
    return None


class PublicTutorSerializer(serializers.ModelSerializer):
    """
    Everything here is safe to show to anyone. Deliberately NOT included:
    WhatsApp number, email, date of birth, Matric marks and documents.
    """

    full_name = serializers.CharField(read_only=True)
    area = AreaSerializer(read_only=True)
    subjects = serializers.SerializerMethodField()
    verification = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = TutorProfile
        fields = [
            "id", "full_name", "bio", "hourly_rate", "teaches_online", "teaches_in_person",
            "area", "availability", "subjects", "verification", "photo_url",
        ]

    def get_subjects(self, profile):
        items = approved_subjects().filter(application__user=profile.user).select_related("subject")
        return [{"id": i.subject_id, "name": i.subject.name, "grades": i.grades}
                for i in sorted(items, key=lambda i: i.subject.name)]

    def get_verification(self, profile):
        pathway = profile.user.tutor_application.pathway
        return "Qualified teacher" if pathway == Pathway.TEACHER else "Matric results verified"

    def get_photo_url(self, profile):
        return photo_url(profile)


class OwnProfileSerializer(serializers.ModelSerializer):
    """The tutor editing their own profile."""

    area = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.filter(is_active=True), allow_null=True, required=False
    )
    area_detail = AreaSerializer(source="area", read_only=True)
    missing_fields = serializers.SerializerMethodField()
    is_listed = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = TutorProfile
        fields = [
            "bio", "hourly_rate", "teaches_online", "teaches_in_person", "area", "area_detail",
            "availability", "whatsapp_number", "photo_status", "photo_note", "photo_url",
            "missing_fields", "is_listed",
        ]
        read_only_fields = ["photo_status", "photo_note"]

    def get_missing_fields(self, profile):
        return profile.missing_fields()

    def get_is_listed(self, profile):
        from .queries import discoverable_profiles
        return discoverable_profiles().filter(pk=profile.pk).exists()

    def get_photo_url(self, profile):
        # The owner can see their own pending photo through their own endpoint.
        return reverse("own-photo") + f"?v={int(profile.updated_at.timestamp())}" if profile.photo else None

    def validate_bio(self, value):
        value = value.strip()
        if len(value) > MAX_BIO_LENGTH:
            raise serializers.ValidationError(f"Keep your bio under {MAX_BIO_LENGTH} characters.")
        return value

    def validate_hourly_rate(self, value):
        if value is not None and not MIN_HOURLY_RATE <= value <= MAX_HOURLY_RATE:
            raise serializers.ValidationError(f"Set a rate between R{MIN_HOURLY_RATE} and R{MAX_HOURLY_RATE} per hour.")
        return value

    def validate_whatsapp_number(self, value):
        if not value.strip():
            return ""
        normalised = normalise_sa_mobile(value)
        if not normalised:
            raise serializers.ValidationError("Enter a South African mobile number, e.g. 082 123 4567.")
        return normalised

    def validate(self, attrs):
        in_person = attrs.get("teaches_in_person", getattr(self.instance, "teaches_in_person", False))
        area = attrs.get("area", getattr(self.instance, "area", None))
        if in_person and area is None:
            raise serializers.ValidationError({"area": ["Choose the area where you give in-person lessons."]})
        return attrs

