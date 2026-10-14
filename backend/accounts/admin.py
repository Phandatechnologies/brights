from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "first_name", "last_name", "account_type", "is_active", "is_staff", "date_joined"]
    list_filter = ["account_type", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["date_joined", "last_login", "guardian_consent_given_at"]

    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal details", {"fields": ["first_name", "last_name", "date_of_birth", "account_type"]}),
        ("Guardian consent (minors)", {"fields": ["guardian_name", "guardian_consent_given_at"]}),
        ("Access", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        ("Dates", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (None, {
            "classes": ["wide"],
            "fields": ["email", "first_name", "last_name", "date_of_birth", "account_type",
                       "password1", "password2"],
        }),
    ]
