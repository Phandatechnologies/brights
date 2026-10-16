from django.contrib.auth import authenticate, login, logout, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .emails import send_password_reset_email, send_verification_email
from .models import User
from .serializers import (
    LoginSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, RegisterSerializer,
    TokenSerializer, UserSerializer,
)
from .tokens import email_verification_token, password_reset_token, user_from_uid


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
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save()
            transaction.on_commit(lambda: send_verification_email(user))
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
            # Suspended (inactive) and temporarily locked accounts also end up here.
            return Response(
                {"detail": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST
            )
        if user.is_staff:
            # Admin accounts can download ID documents, so they only sign in through the
            # admin site, which has its own stricter rate limit.
            return Response({"detail": "Admin accounts sign in through the admin site."},
                            status=status.HTTP_403_FORBIDDEN)
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


INVALID_LINK = {"detail": "This link is invalid or has expired. Please request a new one."}


@method_decorator(csrf_protect, name="dispatch")
class VerifyEmailView(APIView):
    """POST /api/auth/verify-email/ {uid, token} — from the link in the verification email."""

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        data = TokenSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = user_from_uid(data.validated_data["uid"])
        if not user:
            return Response(INVALID_LINK, status=status.HTTP_400_BAD_REQUEST)
        if user.email_verified:
            # Already verified: the token can't be checked any more (it was single-use),
            # so only confirm this to the account owner themselves.
            if request.user.is_authenticated and request.user.pk == user.pk:
                return Response({"verified": True})
            return Response(INVALID_LINK, status=status.HTTP_400_BAD_REQUEST)
        if not email_verification_token.check_token(user, data.validated_data["token"]):
            return Response(INVALID_LINK, status=status.HTTP_400_BAD_REQUEST)
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at"])
        return Response({"verified": True})


class ResendVerificationView(APIView):
    """POST /api/auth/resend-verification/ — the logged-in user asks for a new link."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"

    def post(self, request):
        if not request.user.email_verified:
            send_verification_email(request.user)
        return Response({"sent": True})


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/ {email}
    Always answers the same way, so it can't be used to find out who has an account.
    """

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        data = PasswordResetRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = User.objects.filter(email=data.validated_data["email"].strip().lower(), is_active=True).first()
        if user:
            send_password_reset_email(user)
        return Response({"detail": "If an account exists for that email, we've sent a link to reset the password."})


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    """POST /api/auth/password-reset/confirm/ {uid, token, new_password}"""

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        data = PasswordResetConfirmSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = user_from_uid(data.validated_data["uid"])
        if not user or not user.is_active or not password_reset_token.check_token(user, data.validated_data["token"]):
            return Response(INVALID_LINK, status=status.HTTP_400_BAD_REQUEST)
        try:
            password_validation.validate_password(data.validated_data["new_password"], user=user)
        except DjangoValidationError as exc:
            return Response({"new_password": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data.validated_data["new_password"])  # also logs out other sessions
        if not user.email_verified:
            user.email_verified_at = timezone.now()  # they proved they can read this inbox
        user.save()
        return Response({"detail": "Your password has been changed. You can now log in."})
