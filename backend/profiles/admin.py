from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .models import Area, TutorProfile
from .rules import PhotoStatus


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ["name", "province", "is_active"]
    list_filter = ["province", "is_active"]
    search_fields = ["name"]


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    """
    Profiles are written by tutors. Admins only moderate photos here
    (select profiles, then use the 'Approve photo' / 'Reject photo' actions).
    """

    list_display = ["tutor", "photo_preview", "photo_status", "hourly_rate", "area", "teaches_online", "teaches_in_person"]
    list_filter = ["photo_status", "teaches_online", "teaches_in_person", "area__province"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    actions = ["approve_photos", "reject_photos"]
    fields = ["user", "photo_large", "photo_status", "photo_note", "bio", "hourly_rate",
              "teaches_online", "teaches_in_person", "area", "availability", "whatsapp_number", "updated_at"]

    def get_readonly_fields(self, request, obj=None):
        # Only the photo decision fields can be edited by admins.
        return [f for f in self.fields if f not in ("photo_status", "photo_note")]

    def has_add_permission(self, request):
        return False

    @admin.display(description="Tutor", ordering="user__first_name")
    def tutor(self, obj):
        return f"{obj.full_name} ({obj.user.email})"

    @admin.display(description="Photo")
    def photo_preview(self, obj):
        if not obj.photo:
            return "—"
        url = reverse("staff-tutor-photo", args=[obj.pk])
        return format_html('<img src="{}" alt="" style="height:48px;width:48px;object-fit:cover;border-radius:50%">', url)

    @admin.display(description="Photo")
    def photo_large(self, obj):
        if not obj.photo:
            return "No photo"
        url = reverse("staff-tutor-photo", args=[obj.pk])
        return format_html('<img src="{}" alt="" style="max-width:320px;border-radius:8px">', url)

    @admin.action(description="Approve selected photos")
    def approve_photos(self, request, queryset):
        count = queryset.exclude(photo="").update(photo_status=PhotoStatus.APPROVED, photo_note="")
        self.message_user(request, f"Approved {count} photo(s).", messages.SUCCESS)

    @admin.action(description="Reject selected photos (then add a reason on each profile)")
    def reject_photos(self, request, queryset):
        count = queryset.exclude(photo="").update(photo_status=PhotoStatus.REJECTED)
        self.message_user(request, f"Rejected {count} photo(s). Open each profile to add a reason the tutor will see.", messages.WARNING)
