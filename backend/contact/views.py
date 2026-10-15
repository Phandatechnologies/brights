from datetime import timedelta

from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.rules import AccountType
from profiles.models import TutorProfile
from profiles.queries import approved_subjects, discoverable_profiles

from .models import ContactEvent, SafetyAcknowledgement
from .rules import MAX_NEW_TUTORS_PER_DAY, SAFETY_GUIDANCE_VERSION, opening_message, whatsapp_url


class CanContactTutors(BasePermission):
    """Logged-in, active learners and parents. Tutors and staff accounts can't contact tutors."""

    message = "Only learner and parent accounts can contact tutors."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active
                    and user.account_type in (AccountType.LEARNER, AccountType.PARENT))


def needs_safety_ack(user) -> bool:
    return (user.account_type == AccountType.LEARNER and user.is_minor
            and not SafetyAcknowledgement.objects.filter(user=user, version=SAFETY_GUIDANCE_VERSION).exists())


class ContactRequestSerializer(serializers.Serializer):
    subject = serializers.IntegerField(required=False, allow_null=True)
    grade = serializers.IntegerField(required=False, allow_null=True, min_value=8, max_value=12)


class ContactTutorView(APIView):
    """
    POST /api/tutors/<id>/contact/  {"subject": <id>?, "grade": <8-12>?}
    Returns the WhatsApp link (which contains the tutor's number) and logs the contact.
    """

    permission_classes = [CanContactTutors]

    def post(self, request, pk):
        tutor = get_object_or_404(discoverable_profiles(), pk=pk)  # suspended/unlisted tutors → 404
        user = request.user

        if needs_safety_ack(user):
            return Response(
                {"code": "safety_ack_required", "detail": "Please read the safety guidance first."},
                status=status.HTTP_409_CONFLICT,
            )

        since = timezone.now() - timedelta(hours=24)
        recent = set(ContactEvent.objects.filter(requester=user, created_at__gte=since).values_list("tutor_id", flat=True))
        if tutor.pk not in recent and len(recent) >= MAX_NEW_TUTORS_PER_DAY:
            return Response(
                {"detail": f"You can contact up to {MAX_NEW_TUTORS_PER_DAY} new tutors a day. Please try again tomorrow."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        data = ContactRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        # Only accept a subject/grade this tutor is actually approved for; otherwise ignore it.
        choice = None
        if data.validated_data.get("subject"):
            choice = approved_subjects().filter(application__user=tutor.user,
                                                subject_id=data.validated_data["subject"]).select_related("subject").first()
        grade = data.validated_data.get("grade")
        if grade and choice and grade not in choice.grades:
            grade = None

        ContactEvent.objects.create(
            requester=user, tutor=tutor, subject=choice.subject if choice else None,
            grade=grade, requester_was_minor=user.is_minor,
        )
        message = opening_message(
            tutor_first_name=tutor.user.first_name, account_type=user.account_type, is_minor=user.is_minor,
            subject_name=choice.subject.name if choice else None, grade=grade,
        )
        return Response({"whatsapp_url": whatsapp_url(tutor.whatsapp_number, message), "message": message})


class SafetyAcknowledgementView(APIView):
    """GET: does this user still need to confirm? POST: confirm the current safety guidance."""

    permission_classes = [CanContactTutors]

    def get(self, request):
        return Response({"required": needs_safety_ack(request.user), "version": SAFETY_GUIDANCE_VERSION})

    def post(self, request):
        SafetyAcknowledgement.objects.get_or_create(user=request.user, version=SAFETY_GUIDANCE_VERSION)
        return Response({"required": False, "version": SAFETY_GUIDANCE_VERSION}, status=status.HTTP_201_CREATED)


class ContactHistoryView(APIView):
    """GET /api/contact/history/ — tutors this user has contacted (most recent first)."""

    permission_classes = [CanContactTutors]

    def get(self, request):
        rows = (ContactEvent.objects.filter(requester=request.user)
                .values("tutor_id").annotate(last=Max("created_at")).order_by("-last")[:20])
        listed = set(discoverable_profiles().filter(pk__in=[r["tutor_id"] for r in rows]).values_list("pk", flat=True))
        names = {p.pk: p.full_name for p in TutorProfile.objects.select_related("user").filter(pk__in=[r["tutor_id"] for r in rows])}
        return Response([
            {"tutor_id": r["tutor_id"], "name": names.get(r["tutor_id"], "Tutor"),
             "last_contacted": r["last"], "available": r["tutor_id"] in listed}
            for r in rows
        ])
