from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import EmailVerified
from accounts.rules import AccountType
from contact.models import ContactEvent
from profiles.models import TutorProfile
from profiles.queries import discoverable_profiles

from . import notifications
from .models import Report
from .rules import MAX_DESCRIPTION, MAX_REPORTS_PER_DAY, MIN_DESCRIPTION, Category, ReportStatus


class ReportSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=Category.CHOICES)
    description = serializers.CharField(min_length=MIN_DESCRIPTION, max_length=MAX_DESCRIPTION, trim_whitespace=True,
                                        error_messages={"min_length": f"Please describe what happened in at least {MIN_DESCRIPTION} characters."})
    incident_date = serializers.DateField(required=False, allow_null=True)

    def validate_incident_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("The date can't be in the future.")
        return value


class ReportTutorView(APIView):
    """
    POST /api/tutors/<id>/report/  {category, description, incident_date?}
    Any logged-in user may report a tutor who is listed, or whom they have contacted
    (so a tutor already hidden by an earlier report can still be reported).
    """

    permission_classes = [IsAuthenticated, EmailVerified]

    def post(self, request, pk):
        user = request.user
        tutor = get_object_or_404(TutorProfile.objects.select_related("user"), pk=pk)
        visible = discoverable_profiles().filter(pk=pk).exists()
        contacted = ContactEvent.objects.filter(requester=user, tutor=tutor).exists()
        if not (visible or contacted):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if tutor.user_id == user.pk:
            return Response({"detail": "You can't report yourself."}, status=status.HTTP_400_BAD_REQUEST)

        if Report.objects.filter(reporter=user, tutor=tutor, status=ReportStatus.OPEN).exists():
            return Response({"detail": "You've already reported this tutor. Our team is reviewing it."},
                            status=status.HTTP_409_CONFLICT)
        since = timezone.now() - timedelta(hours=24)
        if Report.objects.filter(reporter=user, created_at__gte=since).count() >= MAX_REPORTS_PER_DAY:
            return Response({"detail": "You've sent several reports today. Please try again tomorrow, or email us."},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        data = ReportSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        urgent = data.validated_data["category"] in Category.URGENT
        # Only someone with a real connection to the tutor can hide them instantly.
        holds = urgent and contacted and user.account_type in (AccountType.LEARNER, AccountType.PARENT)
        with transaction.atomic():
            report = Report.objects.create(
                reporter=user, tutor=tutor, **data.validated_data,
                is_urgent=urgent, holds_tutor=holds,
                reporter_was_minor=bool(getattr(user, "is_minor", False)),
            )
            transaction.on_commit(lambda: notifications.notify_reporter_received(report))
            if report.is_urgent:
                transaction.on_commit(lambda: notifications.notify_admins_urgent(report))
        return Response({"id": report.pk, "urgent": report.is_urgent, "tutor_hidden": report.holds_tutor},
                        status=status.HTTP_201_CREATED)
