from rest_framework.permissions import BasePermission

from accounts.rules import AccountType


class IsTutorAccount(BasePermission):
    """Logged-in, active user whose account type is Tutor."""

    message = "Only tutor accounts can do this."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.is_active
            and user.account_type == AccountType.TUTOR
        )


class IsStaff(BasePermission):
    """Brights administrators only (is_staff). Never grantable through the API."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_staff)
