from rest_framework import serializers

from .models import ApplicationDocument, ApplicationSubject, Subject, TutorApplication
from .rules import REQUIRED_DOCUMENTS, DocumentKind, Pathway, grades_error, mark_error
from .uploads import MAX_UPLOAD_BYTES, safe_display_name, sniff_file_type


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


class ApplicationSubjectSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = ApplicationSubject
        fields = ["id", "subject", "matric_mark", "grades", "decision", "decision_note"]


class DocumentSerializer(serializers.ModelSerializer):
    """What the tutor sees about their own uploads. No file path or URL is ever included."""

    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = ApplicationDocument
        fields = ["id", "kind", "kind_label", "original_name", "content_type", "size", "uploaded_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    subjects = ApplicationSubjectSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    is_editable = serializers.BooleanField(read_only=True)
    required_documents = serializers.SerializerMethodField()
    reapply_available_from = serializers.SerializerMethodField()

    class Meta:
        model = TutorApplication
        fields = [
            "id", "pathway", "status", "status_label", "is_editable",
            "sace_number", "qualification_name", "reviewer_message",
            "subjects", "documents", "required_documents",
            "reapply_available_from", "submitted_at", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_reapply_available_from(self, application):
        from .services import reapply_available_from
        return reapply_available_from(application)

    def get_required_documents(self, application):
        labels = dict(DocumentKind.CHOICES)
        uploaded = {d.kind for d in application.documents.all()}
        return [
            {"kind": kind, "label": labels[kind], "uploaded": kind in uploaded}
            for kind in REQUIRED_DOCUMENTS[application.pathway]
        ]


class SubjectChoiceSerializer(serializers.Serializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.filter(is_active=True))
    matric_mark = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    grades = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class ApplicationUpdateSerializer(serializers.Serializer):
    """
    Fields a tutor may change while the application is a draft or needs more info.
    Status, reviewer fields and the owner can never be set here.
    """

    pathway = serializers.ChoiceField(choices=Pathway.CHOICES, required=False)
    sace_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    qualification_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    subjects = SubjectChoiceSerializer(many=True, required=False)

    def validate(self, attrs):
        pathway = attrs.get("pathway", self.instance.pathway)
        subjects = attrs.get("subjects")
        if subjects is not None:
            ids = [s["subject"].id for s in subjects]
            if len(ids) != len(set(ids)):
                raise serializers.ValidationError({"subjects": ["Each subject can only be added once."]})
            errors = {}
            for index, choice in enumerate(subjects):
                problem = mark_error(pathway, choice.get("matric_mark")) or grades_error(choice["grades"])
                if problem:
                    errors[str(index)] = [f"{choice['subject'].name}: {problem}"]
            if errors:
                raise serializers.ValidationError({"subjects": errors})
        elif "pathway" in attrs and attrs["pathway"] != self.instance.pathway:
            # Switching pathway: existing subjects must still satisfy the new pathway's rules.
            for item in self.instance.subjects.select_related("subject"):
                problem = mark_error(pathway, item.matric_mark)
                if problem:
                    raise serializers.ValidationError(
                        {"subjects": [f"{item.subject.name}: {problem}"]}
                    )
        return attrs

    def update(self, application, validated_data):
        subjects = validated_data.pop("subjects", None)
        for field, value in validated_data.items():
            setattr(application, field, value)
        if application.pathway == Pathway.ACADEMIC:
            # Data minimisation: teacher-only details aren't kept for academic tutors.
            application.sace_number = ""
            application.qualification_name = ""
        application.save()

        if subjects is not None:
            application.subjects.all().delete()
            ApplicationSubject.objects.bulk_create(
                ApplicationSubject(
                    application=application,
                    subject=choice["subject"],
                    matric_mark=(choice.get("matric_mark") if application.pathway == Pathway.ACADEMIC else None),
                    grades=sorted(choice["grades"]),
                )
                for choice in subjects
            )
        elif application.pathway == Pathway.TEACHER:
            application.subjects.update(matric_mark=None)
        return application


class DocumentUploadSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=DocumentKind.CHOICES)
    file = serializers.FileField()

    def validate_file(self, uploaded):
        if uploaded.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("Files must be 5 MB or smaller.")
        if uploaded.size == 0:
            raise serializers.ValidationError("This file is empty.")
        content_type, extension = sniff_file_type(uploaded)
        if content_type is None:
            raise serializers.ValidationError("Upload a PDF, JPG or PNG file.")
        uploaded.detected = (content_type, extension)
        return uploaded

    def validate_kind(self, kind):
        application = self.context["application"]
        if kind not in REQUIRED_DOCUMENTS[application.pathway]:
            raise serializers.ValidationError("This document isn't needed for your application type.")
        return kind
