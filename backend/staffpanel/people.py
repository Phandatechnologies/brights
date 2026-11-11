"""
Staff actions on accounts: block / unblock login and resend the confirmation email.

Each action is written to Django's admin history (LogEntry), so it also shows in the
Django admin's history for that user, with who did it and why.
"""

from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.emails import send_verification_email
from accounts.models import User


def _record(staff, user, message):
    LogEntry.objects.log_actions(user_id=staff.pk, queryset=[user], action_flag=CHANGE,
                                 change_message=message, single_object=True)


def history(user, limit=20):
    entries = (LogEntry.objects.filter(content_type=ContentType.objects.get_for_model(User), object_id=str(user.pk))
               .select_related("user").order_by("-action_time")[:limit])
    return [{"when": e.action_time, "by": e.user.email if e.user else None, "what": e.get_change_message()} for e in entries]


def _check(staff, user):
    if not (staff and staff.is_active and staff.is_staff):
        raise PermissionDenied("Only the Brights team can do this.")
    if user.pk == staff.pk:
        raise PermissionDenied("You can't change your own account here.")
    if (user.is_staff or user.is_superuser) and not staff.is_superuser:
        raise PermissionDenied("Only the account owner can change another team member's account.")


@transaction.atomic
def block(user_id, staff, reason):
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Write why you're blocking this account (only the team sees it).")
    user = User.objects.select_for_update().get(pk=user_id)
    _check(staff, user)
    if not user.is_active:
        raise ValidationError("This account is already blocked.")
    user.is_active = False  # can't log in; existing sessions stop working; tutors drop out of search
    user.save(update_fields=["is_active"])
    _record(staff, user, f"Blocked login: {reason}")
    return user


@transaction.atomic
def unblock(user_id, staff, reason=""):
    user = User.objects.select_for_update().get(pk=user_id)
    _check(staff, user)
    if user.is_active:
        raise ValidationError("This account isn't blocked.")
    user.is_active = True
    user.save(update_fields=["is_active"])
    _record(staff, user, f"Unblocked login{': ' + reason.strip() if (reason or '').strip() else ''}")
    return user


def resend_confirmation(user_id, staff):
    user = User.objects.get(pk=user_id)
    if not (staff and staff.is_active and staff.is_staff):
        raise PermissionDenied("Only the Brights team can do this.")
    if user.email_verified:
        raise ValidationError("This email address is already confirmed.")
    if not send_verification_email(user):
        raise ValidationError("We couldn't send the email just now. Please try again in a few minutes.")
    _record(staff, user, "Sent a new email confirmation link")
    return user
