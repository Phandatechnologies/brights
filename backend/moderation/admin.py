from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from contact.models import ContactEvent

from . import services
from .models import Report
from .rules import ReportStatus


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Report queue: urgent first, then oldest. Reports are handled on the review page."""

    list_display = ["urgent_flag", "id", "category", "tutor_name", "reporter", "created_at", "status", "outcome", "review_link"]
    list_display_links = ["id"]
    list_filter = ["status", "is_urgent", "category", "outcome"]
    search_fields = ["tutor__user__email", "tutor__user__first_name", "tutor__user__last_name", "reporter__email", "description"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("tutor__user", "reporter")

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Show open reports by default.
        if "status__exact" not in request.GET and not request.GET.get("_changelist_filters") and request.method == "GET" and not request.GET:
            return redirect(f"{request.path}?status__exact=open")
        return super().changelist_view(request, extra_context)

    @admin.display(description="", ordering="is_urgent")
    def urgent_flag(self, obj):
        return format_html('<strong style="color:#ba2121">URGENT</strong>') if obj.is_urgent else ""

    @admin.display(description="Tutor")
    def tutor_name(self, obj):
        return obj.tutor.full_name

    @admin.display(description="Review")
    def review_link(self, obj):
        return format_html('<a class="button" href="{}">Open</a>', reverse("admin:moderation_report_review", args=[obj.pk]))

    def get_urls(self):
        return [path("<int:pk>/review/", self.admin_site.admin_view(self.review_view), name="moderation_report_review")] + super().get_urls()

    def review_view(self, request, pk):
        report = get_object_or_404(Report.objects.select_related("tutor__user", "reporter", "closed_by"), pk=pk)
        if not self.has_view_permission(request, report):
            raise PermissionDenied

        form = {"notes": "", "message": ""}
        if request.method == "POST":
            action = request.POST.get("action")
            form = {"notes": request.POST.get("notes", ""), "message": request.POST.get("message", "")}
            handlers = {
                "dismiss": lambda: services.dismiss(report.pk, request.user, form["notes"]),
                "warn": lambda: services.warn(report.pk, request.user, form["message"], form["notes"]),
                "suspend": lambda: services.suspend(report.pk, request.user, form["message"], form["notes"]),
            }
            try:
                if action not in handlers:
                    raise ValidationError("Unknown action.")
                handlers[action]()
                messages.success(request, "Report closed. The reporter has been told the review is finished.")
                return redirect("admin:moderation_report_review", pk=report.pk)
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            except PermissionDenied as exc:
                messages.error(request, str(exc) or "You can't do that.")

        tutor_user = report.tutor.user
        application = getattr(tutor_user, "tutor_application", None)
        contacts = (ContactEvent.objects.filter(requester=report.reporter, tutor=report.tutor).select_related("subject")
                    if report.reporter else ContactEvent.objects.none())
        other_reports = Report.objects.filter(tutor=report.tutor).exclude(pk=report.pk).select_related("reporter")
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": f"Report #{report.pk}",
            "report": report,
            "tutor_user": tutor_user,
            "application": application,
            "application_url": reverse("admin:tutors_tutorapplication_review", args=[application.pk]) if application else None,
            "contacts": contacts,
            "other_reports": other_reports,
            "is_open": report.status == ReportStatus.OPEN,
            "is_own": tutor_user.pk == request.user.pk,
            "form": form,
        }
        return TemplateResponse(request, "admin/moderation/review.html", context)
