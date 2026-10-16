from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class EmailVerified(BasePermission):
    """
    Blocks actions that need a real, reachable email address (contacting tutors,
    reporting, submitting a tutor application) until the user verifies their email.
    """

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated and not user.email_verified:
            raise PermissionDenied({
                "code": "email_unverified",
                "detail": "Please confirm your email address first. Check your inbox for the link we sent you.",
            })
        return True
