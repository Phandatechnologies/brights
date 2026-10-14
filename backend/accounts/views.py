from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """
    GET /api/auth/csrf/
    Sets the csrftoken cookie. The frontend calls this once on start-up and then
    sends the token back in the X-CSRFToken header on every POST/PUT/PATCH/DELETE.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


# DRF only checks CSRF for already-logged-in users, so the anonymous endpoints
# below are protected explicitly with csrf_protect.
@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    """POST /api/auth/register/ — create an account and log in."""

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    """POST /api/auth/login/"""

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"].strip().lower(),
            password=serializer.validated_data["password"],
        )
        if user is None:
            # Same message whether the email exists or not, so accounts can't be discovered.
            # Suspended (inactive) accounts also end up here.
            return Response(
                {"detail": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST
            )
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    """POST /api/auth/logout/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ — the logged-in user, or 403 if not logged in."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
