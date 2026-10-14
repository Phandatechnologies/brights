"""
Tutor eligibility rules (Brights brief, section 4). Plain Python so they are
easy to read and test. The API calls these; it never re-implements them.
"""

MIN_SUBJECT_MARK = 60          # Pathway A: at least 60% in every subject offered (inclusive)
MAX_MARK = 100
ALLOWED_GRADES = (8, 9, 10, 11, 12)


class Pathway:
    ACADEMIC = "academic"      # Matric results
    TEACHER = "teacher"        # Qualified teacher

    CHOICES = [
        (ACADEMIC, "Academic tutor (Matric results)"),
        (TEACHER, "Qualified teacher"),
    ]


class Status:
    DRAFT = "draft"
    PENDING = "pending"
    MORE_INFO = "more_info"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

    CHOICES = [
        (DRAFT, "Draft"),
        (PENDING, "Pending review"),
        (MORE_INFO, "More information required"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (SUSPENDED, "Suspended"),
    ]

    # The tutor may only change their application in these states.
    EDITABLE = (DRAFT, MORE_INFO)


class SubjectDecision:
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"

    CHOICES = [
        (PENDING, "Not reviewed yet"),
        (APPROVED, "Approved"),
        (DECLINED, "Declined"),
    ]


REAPPLY_AFTER_DAYS = 30  # a rejected tutor may start again after this many days


class DocumentKind:
    ID_DOCUMENT = "id_document"
    MATRIC_RESULTS = "matric_results"
    TEACHING_QUALIFICATION = "teaching_qualification"
    SACE_CERTIFICATE = "sace_certificate"

    CHOICES = [
        (ID_DOCUMENT, "ID document or passport"),
        (MATRIC_RESULTS, "Matric (NSC) certificate or statement of results"),
        (TEACHING_QUALIFICATION, "Teaching qualification"),
        (SACE_CERTIFICATE, "SACE registration certificate"),
    ]


REQUIRED_DOCUMENTS = {
    Pathway.ACADEMIC: [DocumentKind.ID_DOCUMENT, DocumentKind.MATRIC_RESULTS],
    Pathway.TEACHER: [
        DocumentKind.ID_DOCUMENT,
        DocumentKind.TEACHING_QUALIFICATION,
        DocumentKind.SACE_CERTIFICATE,
    ],
}


def mark_error(pathway, mark):
    """Return an error message if this mark doesn't allow tutoring the subject, else None."""
    if pathway != Pathway.ACADEMIC:
        return None  # Teachers qualify through their qualifications, not Matric marks.
    if mark is None:
        return "Enter your Matric mark for this subject."
    if not 0 <= mark <= MAX_MARK:
        return "Marks must be between 0 and 100."
    if mark < MIN_SUBJECT_MARK:
        return f"You need at least {MIN_SUBJECT_MARK}% in a subject to tutor it."
    return None


def grades_error(grades):
    if not grades:
        return "Choose at least one grade."
    if len(set(grades)) != len(grades):
        return "Each grade can only be chosen once."
    if any(g not in ALLOWED_GRADES for g in grades):
        return "Grades must be between 8 and 12."
    return None


def submission_errors(*, pathway, subjects, document_kinds, sace_number, qualification_name):
    """
    Everything that must be true before an application can be submitted.
    `subjects` is a list of (mark, grades) tuples; `document_kinds` a set of uploaded kinds.
    Returns {field: [messages]}; empty means ready to submit.
    """
    errors = {}

    if not subjects:
        errors["subjects"] = ["Add at least one subject you want to tutor."]
    else:
        problems = []
        for mark, grades in subjects:
            problem = mark_error(pathway, mark) or grades_error(grades)
            if problem:
                problems.append(problem)
        if problems:
            errors["subjects"] = sorted(set(problems))

    missing = [k for k in REQUIRED_DOCUMENTS[pathway] if k not in document_kinds]
    if missing:
        labels = dict(DocumentKind.CHOICES)
        errors["documents"] = [f"Upload your {labels[k]}." for k in missing]

    if pathway == Pathway.TEACHER:
        if not (sace_number or "").strip():
            errors["sace_number"] = ["Enter your SACE registration number."]
        if not (qualification_name or "").strip():
            errors["qualification_name"] = ["Enter the name of your teaching qualification."]

    return errors
