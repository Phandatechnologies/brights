"""
API for the staff area of the web app (/staff).

These views only read data and call the existing workflow functions
(tutors.services, moderation.services). They never change a status themselves,
so every decision is still checked, logged in the history and emailed exactly
as before. Staff only: is_staff + active, never grantable through the API.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from profiles.models import TutorProfile
from profiles.rules import PhotoStatus
from tutors import services
from tutors.models import TutorApplication
from tutors.permissions import IsStaff
from tutors.rules import Status

from .serializers import application_detail, application_row


def error_response(exc):
    """Turn a workflow error into {"non_field_errors": [...]} so the web app shows every message."""
    if isinstance(exc, PermissionDenied):
        return Response({"non_field_errors": [str(exc) or "You can't do that."]}, status=status.HTTP_403_FORBIDDEN)
    return Response({"non_field_errors": exc.messages}, status=status.HTTP_400_BAD_REQUEST)


class OverviewView(APIView):
    """GET /api/staff/overview/ — what needs attention, plus a few platform totals."""

    permission_classes = [IsStaff]

    def get(self, request):
        apps = TutorApplication.objects.aggregate(
            pending=Count("pk", filter=Q(status=Status.PENDING)),
            more_info=Count("pk", filter=Q(status=Status.MORE_INFO)),
            approved=Count("pk", filter=Q(status=Status.APPROVED)),
        )
        oldest = (TutorApplication.objects.filter(status=Status.PENDING)
                  .order_by("submitted_at").values_list("submitted_at", flat=True).first())
        people = User.objects.filter(is_staff=False, is_active=True).aggregate(
            learners=Count("pk", filter=Q(account_type="learner")),
            parents=Count("pk", filter=Q(account_type="parent")),
            tutors=Count("pk", filter=Q(account_type="tutor")),
        )
        return Response({
            "applications_pending": apps["pending"],
            "applications_more_info": apps["more_info"],
            "oldest_pending_days": (timezone.now() - oldest).days if oldest else None,
            "photos_waiting": TutorProfile.objects.filter(photo_status=PhotoStatus.PENDING).exclude(photo="").count(),
            "totals": {**people, "approved_tutors": apps["approved"]},
        })


class ApplicationPagination(PageNumberPagination):
    page_size = 20


STATUS_FILTERS = {
    "pending": [Status.PENDING],
    "more_info": [Status.MORE_INFO],
    "approved": [Status.APPROVED],
    "rejected": [Status.REJECTED],
    "suspended": [Status.SUSPENDED],
    "draft": [Status.DRAFT],
}


class ApplicationListView(APIView):
    """
    GET /api/staff/applications/?status=pending&q=thabo&page=1
    Waiting applications are listed oldest first (a fair queue); others newest first.
    """

    permission_classes = [IsStaff]

    def get(self, request):
        wanted = request.query_params.get("status", "pending")
        queryset = TutorApplication.objects.select_related("user").annotate(subject_count=Count("subjects"))
        if wanted in STATUS_FILTERS:
            queryset = queryset.filter(status__in=STATUS_FILTERS[wanted])
        query = (request.query_params.get("q") or "").strip()
        if query:
            for word in query.split():
                queryset = queryset.filter(
                    Q(user__first_name__icontains=word) | Q(user__last_name__icontains=word) | Q(user__email__icontains=word))
        if wanted == "pending":
            queryset = queryset.order_by("submitted_at", "pk")
        else:
            queryset = queryset.order_by("-updated_at", "-pk")
        paginator = ApplicationPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response([application_row(a) for a in page])


class ApplicationDetailView(APIView):
    """GET /api/staff/applications/<id>/ — everything a reviewer needs on one page."""

    permission_classes = [IsStaff]

    def get(self, request, pk):
        application = get_object_or_404(TutorApplication.objects.select_related("user", "reviewed_by"), pk=pk)
        return Response(application_detail(application, request.user))


class ApplicationDecisionView(APIView):
    """
    POST /api/staff/applications/<id>/decide/
    {"action": "approve" | "request_info" | "reject" | "suspend" | "reinstate",
     "message": "...", "decisions": [{"id": <subject row id>, "decision": "approved" | "declined", "note": "..."}]}
    """

    permission_classes = [IsStaff]

    def post(self, request, pk):
        application = get_object_or_404(TutorApplication, pk=pk)
        action = request.data.get("action")
        message = str(request.data.get("message") or "")
        decisions = {}
        for row in request.data.get("decisions") or []:
            if isinstance(row, dict):
                try:
                    decisions[int(row.get("id"))] = (str(row.get("decision") or ""), str(row.get("note") or ""))
                except (TypeError, ValueError):
                    continue
        handlers = {
            "approve": lambda: services.approve(application.pk, request.user, decisions, message),
            "request_info": lambda: services.request_more_info(application.pk, request.user, message),
            "reject": lambda: services.reject(application.pk, request.user, message),
            "suspend": lambda: services.suspend(application.pk, request.user, message),
            "reinstate": lambda: services.reinstate(application.pk, request.user, message),
        }
        if action not in handlers:
            return Response({"non_field_errors": ["Choose what to do with this application."]}, status=400)
        try:
            handlers[action]()
        except (ValidationError, PermissionDenied) as exc:
            return error_response(exc)
        application.refresh_from_db()
        return Response(application_detail(application, request.user))
