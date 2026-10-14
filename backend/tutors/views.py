from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.rules import ADULT_AGE
from .models import ApplicationDocument, Subject, TutorApplication
from .permissions import IsStaff, IsTutorAccount
from . import services
from .rules import Pathway
from .uploads import safe_display_name
from .serializers import (
    ApplicationSerializer, ApplicationUpdateSerializer, DocumentSerializer,
    DocumentUploadSerializer, SubjectSerializer,
)

MAX_DOCUMENTS = 10


def not_editable_response(application):
    return Response(
        {"detail": f"Your application is {application.get_status_display().lower()} and can't be changed right now."},
        status=status.HTTP_409_CONFLICT,
    )


class SubjectListView(APIView):
    """GET /api/subjects/ — public list of subjects tutors can offer."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(SubjectSerializer(Subject.objects.filter(is_active=True), many=True).data)


class MyApplicationView(APIView):
    """
    The logged-in tutor's own application.
    GET    — view it (404 if not started)
    POST   — start a draft: {"pathway": "academic" | "teacher"}
    PATCH  — update while draft / more info required
    """

    permission_classes = [IsTutorAccount]

    def get_application(self, request):
        return get_object_or_404(
            TutorApplication.objects.prefetch_related("subjects__subject", "documents"), user=request.user
        )

    def get(self, request):
        return Response(ApplicationSerializer(self.get_application(request)).data)

    def post(self, request):
        if TutorApplication.objects.filter(user=request.user).exists():
            return Response({"detail": "You already have an application."}, status=status.HTTP_409_CONFLICT)
        pathway = request.data.get("pathway")
        if pathway not in dict(Pathway.CHOICES):
            return Response({"pathway": ["Choose an application type."]}, status=status.HTTP_400_BAD_REQUEST)
        application = TutorApplication.objects.create(user=request.user, pathway=pathway)
        return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        application = self.get_application(request)
        if not application.is_editable:
            return not_editable_response(application)
        serializer = ApplicationUpdateSerializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
        application = self.get_application(request)  # reload with fresh relations
        return Response(ApplicationSerializer(application).data)


def run_service(action, *args):
    """Call a workflow function and turn its errors into API responses."""
    try:
        return action(*args), None
    except DjangoValidationError as exc:
        body = exc.message_dict if hasattr(exc, "error_dict") else {"detail": " ".join(exc.messages)}
        return None, Response(body, status=status.HTTP_400_BAD_REQUEST)
    except DjangoPermissionDenied as exc:
        return None, Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)


class SubmitApplicationView(APIView):
    """POST /api/tutor/application/submit/ — send for review once everything is complete."""

    permission_classes = [IsTutorAccount]

    def post(self, request):
        application = get_object_or_404(TutorApplication, user=request.user)
        if not application.is_editable:
            return not_editable_response(application)
        if request.user.age < ADULT_AGE:  # re-checked here, not only at sign-up
            return Response({"detail": "You must be at least 18 to apply as a tutor."},
                            status=status.HTTP_400_BAD_REQUEST)
        application, error = run_service(services.submit, application.pk, request.user)
        return error or Response(ApplicationSerializer(application).data)


class ReapplyView(APIView):
    """POST /api/tutor/application/reapply/ — start again after a rejection (30-day wait)."""

    permission_classes = [IsTutorAccount]

    def post(self, request):
        application = get_object_or_404(TutorApplication, user=request.user)
        application, error = run_service(services.reapply, application.pk, request.user)
        return error or Response(ApplicationSerializer(application).data)


class DocumentUploadView(APIView):
    """POST /api/tutor/application/documents/ (multipart: kind, file)"""

    permission_classes = [IsTutorAccount]
    parser_classes = [MultiPartParser]

    def post(self, request):
        application = get_object_or_404(TutorApplication, user=request.user)
        if not application.is_editable:
            return not_editable_response(application)
        if application.documents.count() >= MAX_DOCUMENTS:
            return Response({"detail": f"You can upload at most {MAX_DOCUMENTS} documents."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = DocumentUploadSerializer(data=request.data, context={"application": application})
        serializer.is_valid(raise_exception=True)
        uploaded = serializer.validated_data["file"]
        content_type, extension = uploaded.detected

        document = ApplicationDocument(
            application=application,
            kind=serializer.validated_data["kind"],
            original_name=safe_display_name(uploaded.name),
            content_type=content_type,
            size=uploaded.size,
        )
        document._detected_extension = extension  # used by upload_to for the stored name
        document.file.save("upload", uploaded, save=False)
        document.save()
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class DocumentDeleteView(APIView):
    """DELETE /api/tutor/application/documents/<id>/ — tutors can only delete their own."""

    permission_classes = [IsTutorAccount]

    def delete(self, request, pk):
        # Filtering by owner means another tutor's document id simply returns 404.
        document = get_object_or_404(ApplicationDocument, pk=pk, application__user=request.user)
        if not document.application.is_editable:
            return not_editable_response(document.application)
        document.file.delete(save=False)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffDocumentDownloadView(APIView):
    """
    GET /api/staff/documents/<id>/download/
    The ONLY way to read a verification document. Staff only.
    """

    permission_classes = [IsStaff]

    def get(self, request, pk):
        document = get_object_or_404(ApplicationDocument, pk=pk)
        try:
            handle = document.file.open("rb")
        except FileNotFoundError:
            raise Http404("File missing from storage.")
        # ?inline=1 lets reviewers view PDFs/images in the browser instead of downloading.
        inline = request.query_params.get("inline") == "1"
        response = FileResponse(
            handle, as_attachment=not inline, filename=document.original_name, content_type=document.content_type
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response
