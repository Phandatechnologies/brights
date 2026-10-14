from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from . import services
from .models import ApplicationDocument, ApplicationEvent, ApplicationSubject, Subject, TutorApplication
from .rules import MIN_SUBJECT_MARK, Pathway, Status, SubjectDecision


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


class ReadOnlyInline(admin.TabularInline):
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ApplicationSubjectInline(ReadOnlyInline):
    model = ApplicationSubject
    fields = readonly_fields = ["subject", "matric_mark", "grades", "decision", "decision_note"]


class ApplicationDocumentInline(ReadOnlyInline):
    model = ApplicationDocument
    fields = readonly_fields = ["kind", "original_name", "content_type", "size", "uploaded_at", "download"]

    @admin.display(description="File")
    def download(self, document):
        url = reverse("staff-document-download", args=[document.pk])
        return format_html('<a href="{}?inline=1" target="_blank" rel="noopener">View</a> · <a href="{}">Download</a>', url, url)


class ApplicationEventInline(ReadOnlyInline):
    model = ApplicationEvent
    fields = readonly_fields = ["created_at", "actor", "action", "from_status", "to_status", "note"]
    verbose_name_plural = "History"


@admin.register(TutorApplication)
class TutorApplicationAdmin(admin.ModelAdmin):
    """
    Applications are read-only here: status can ONLY change through the review page,
    which uses tutors/services.py so every decision is checked, logged and emailed.
    """

    list_display = ["applicant", "pathway", "status", "submitted_at", "review_link"]
    list_filter = ["status", "pathway"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    ordering = ["submitted_at"]  # oldest first: a fair review queue
    inlines = [ApplicationSubjectInline, ApplicationDocumentInline, ApplicationEventInline]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields] + ["review_link"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # keeps the audit trail intact

    @admin.display(description="Applicant", ordering="user__first_name")
    def applicant(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name} ({obj.user.email})"

    @admin.display(description="Review")
    def review_link(self, obj):
        if obj.status == Status.DRAFT:
            return "Not submitted"
        url = reverse("admin:tutors_tutorapplication_review", args=[obj.pk])
        return format_html('<a class="button" href="{}">Open review</a>', url)

    def get_urls(self):
        custom = [
            path("<int:pk>/review/", self.admin_site.admin_view(self.review_view),
                 name="tutors_tutorapplication_review"),
        ]
        return custom + super().get_urls()

    # --- Review page ------------------------------------------------------------

    def review_view(self, request, pk):
        application = get_object_or_404(
            TutorApplication.objects.select_related("user", "reviewed_by"), pk=pk
        )
        if not self.has_view_permission(request, application):
            raise PermissionDenied

        entered = {}
        if request.method == "POST":
            if not request.user.is_staff:
                raise PermissionDenied
            action = request.POST.get("action")
            message = request.POST.get("message", "")
            subjects = list(application.subjects.all())
            decisions = {
                s.pk: (request.POST.get(f"decision_{s.pk}", ""), request.POST.get(f"note_{s.pk}", ""))
                for s in subjects
            }
            entered = {"message": message, "decisions": decisions}
            handlers = {
                "approve": lambda: services.approve(application.pk, request.user, decisions, message),
                "request_info": lambda: services.request_more_info(application.pk, request.user, message),
                "reject": lambda: services.reject(application.pk, request.user, message),
                "suspend": lambda: services.suspend(application.pk, request.user, message),
                "reinstate": lambda: services.reinstate(application.pk, request.user, message),
            }
            if action not in handlers:
                messages.error(request, "Unknown action.")
            else:
                try:
                    updated = handlers[action]()
                    messages.success(request, f"Done. The application is now '{updated.get_status_display()}' and the tutor has been emailed.")
                    return redirect("admin:tutors_tutorapplication_review", pk=application.pk)
                except ValidationError as exc:
                    for msg in exc.messages:
                        messages.error(request, msg)
                except PermissionDenied as exc:
                    messages.error(request, str(exc) or "You can't do that.")

        subject_rows = []
        for item in application.subjects.select_related("subject"):
            decision, note = entered.get("decisions", {}).get(item.pk, (item.decision, item.decision_note))
            subject_rows.append({
                "item": item,
                "decision": decision,
                "note": note,
                "below_threshold": application.pathway == Pathway.ACADEMIC and (item.matric_mark or 0) < MIN_SUBJECT_MARK,
                "grades": ", ".join(str(g) for g in item.grades),
            })

        documents = [
            {"doc": d, "url": reverse("staff-document-download", args=[d.pk])}
            for d in application.documents.all()
        ]
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": f"Review: {application.user.first_name} {application.user.last_name}",
            "application": application,
            "applicant": application.user,
            "subject_rows": subject_rows,
            "documents": documents,
            "events": application.events.select_related("actor"),
            "message": entered.get("message", ""),
            "is_own": application.user_id == request.user.pk,
            "can_decide": application.status == Status.PENDING,
            "can_suspend": application.status == Status.APPROVED,
            "can_reinstate": application.status == Status.SUSPENDED,
            "APPROVED": SubjectDecision.APPROVED,
            "DECLINED": SubjectDecision.DECLINED,
            "min_mark": MIN_SUBJECT_MARK,
        }
        return TemplateResponse(request, "admin/tutors/review.html", context)


@admin.register(ApplicationEvent)
class ApplicationEventAdmin(admin.ModelAdmin):
    """Audit trail: view only. Nobody can add, change or delete events."""

    list_display = ["created_at", "application", "actor", "action", "from_status", "to_status"]
    list_filter = ["action", "to_status"]
    search_fields = ["application__user__email", "note"]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
