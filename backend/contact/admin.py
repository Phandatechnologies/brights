from django.contrib import admin

from .models import ContactEvent, SafetyAcknowledgement


class ReadOnlyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ContactEvent)
class ContactEventAdmin(ReadOnlyAdmin):
    list_display = ["created_at", "requester", "tutor", "subject", "grade", "requester_was_minor"]
    list_filter = ["requester_was_minor", "created_at"]
    search_fields = ["requester__email", "tutor__user__email"]
    date_hierarchy = "created_at"


@admin.register(SafetyAcknowledgement)
class SafetyAcknowledgementAdmin(ReadOnlyAdmin):
    list_display = ["user", "version", "acknowledged_at"]
    search_fields = ["user__email"]
