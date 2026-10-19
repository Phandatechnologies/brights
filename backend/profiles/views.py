from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from tutors.permissions import IsStaff, IsTutorAccount

from .images import InvalidPhoto, clean_photo
from .insights import record_view, tutor_insights
from .models import Area, TutorProfile
from .queries import discoverable_profiles, search
from .rules import PROVINCES, PhotoStatus
from .serializers import AreaSerializer, OwnProfileSerializer, PublicTutorSerializer


def _photo_response(profile):
    try:
        handle = profile.photo.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404
    response = FileResponse(handle, content_type="image/jpeg")
    response["X-Content-Type-Options"] = "nosniff"
    return response


# --- Public ----------------------------------------------------------------------

class AreaListView(APIView):
    """GET /api/areas/ — provinces and active areas (optionally ?province=gauteng)."""

    permission_classes = [AllowAny]

    def get(self, request):
        areas = Area.objects.filter(is_active=True)
        if request.query_params.get("province"):
            areas = areas.filter(province=request.query_params["province"])
        return Response({
            "provinces": [{"value": v, "label": l} for v, l in PROVINCES],
            "areas": AreaSerializer(areas, many=True).data,
        })


class SearchPagination(PageNumberPagination):
    page_size = 12


class TutorSearchView(ListAPIView):
    """GET /api/tutors/?subject=&grade=&mode=&province=&area=&min_price=&max_price=&sort=&page="""

    permission_classes = [AllowAny]
    serializer_class = PublicTutorSerializer
    pagination_class = SearchPagination

    def get_queryset(self):
        return search(self.request.query_params)


class TutorDetailView(APIView):
    """GET /api/tutors/<id>/ — 404 unless the tutor is currently discoverable."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        profile = get_object_or_404(discoverable_profiles(), pk=pk)
        record_view(request, profile)
        return Response(PublicTutorSerializer(profile).data)


class TutorPhotoView(APIView):
    """GET /api/tutors/<id>/photo/ — only approved photos of discoverable tutors."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        profile = get_object_or_404(discoverable_profiles(), pk=pk, photo_status=PhotoStatus.APPROVED)
        response = _photo_response(profile)
        response["Cache-Control"] = "private, max-age=300"  # short, so hidden tutors' photos disappear quickly
        return response


# --- The tutor's own profile ----------------------------------------------------------

class OwnProfileView(APIView):
    """GET / PATCH /api/tutor/profile/ — created automatically on first use."""

    permission_classes = [IsTutorAccount]

    def get_profile(self, request):
        profile, _ = TutorProfile.objects.get_or_create(user=request.user)
        return profile

    def get(self, request):
        return Response(OwnProfileSerializer(self.get_profile(request)).data)

    def patch(self, request):
        serializer = OwnProfileSerializer(self.get_profile(request), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OwnPhotoView(APIView):
    """
    GET    /api/tutor/profile/photo/ — the tutor's own photo (any status)
    POST   — upload/replace (multipart field "photo"); goes to admin for approval
    DELETE — remove
    """

    permission_classes = [IsTutorAccount]
    parser_classes = [MultiPartParser]
    throttle_scope = "upload"

    def get_throttles(self):
        return super().get_throttles() if self.request.method == "POST" else []

    def get(self, request):
        profile = get_object_or_404(TutorProfile, user=request.user)
        if not profile.photo:
            raise Http404
        response = _photo_response(profile)
        response["Cache-Control"] = "private, no-store"
        return response

    def post(self, request):
        uploaded = request.FILES.get("photo")
        if not uploaded:
            return Response({"photo": ["Choose a photo to upload."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cleaned = clean_photo(uploaded)
        except InvalidPhoto as exc:
            return Response({"photo": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = TutorProfile.objects.get_or_create(user=request.user)
        with transaction.atomic():
            old = profile.photo.name if profile.photo else None
            profile.photo.save("photo.jpg", cleaned, save=False)
            profile.photo_status = PhotoStatus.PENDING
            profile.photo_note = ""
            profile.save()
        if old:
            profile.photo.storage.delete(old)
        return Response(OwnProfileSerializer(profile).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        profile = get_object_or_404(TutorProfile, user=request.user)
        if profile.photo:
            profile.photo.delete(save=False)
        profile.photo_status = PhotoStatus.NONE
        profile.photo_note = ""
        profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffPhotoView(APIView):
    """GET /api/staff/tutor-photos/<profile id>/ — admins viewing photos waiting for approval."""

    permission_classes = [IsStaff]

    def get(self, request, pk):
        profile = get_object_or_404(TutorProfile, pk=pk)
        response = _photo_response(profile)
        response["Cache-Control"] = "private, no-store"
        return response


class OwnInsightsView(APIView):
    """GET /api/tutor/insights/ — this month's and last month's numbers for the tutor's Home."""

    permission_classes = [IsTutorAccount]

    def get(self, request):
        profile, _ = TutorProfile.objects.get_or_create(user=request.user)
        return Response(tutor_insights(profile))
