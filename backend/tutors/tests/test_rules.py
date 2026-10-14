from django.test import SimpleTestCase

from tutors.rules import DocumentKind, Pathway, grades_error, mark_error, submission_errors


class MarkRuleTests(SimpleTestCase):
    """Brief examples: 60% Maths ok, 75% Physical Sciences ok, 59% English not ok."""

    def test_60_percent_is_enough(self):
        self.assertIsNone(mark_error(Pathway.ACADEMIC, 60))

    def test_75_percent_is_enough(self):
        self.assertIsNone(mark_error(Pathway.ACADEMIC, 75))

    def test_100_percent_is_enough(self):
        self.assertIsNone(mark_error(Pathway.ACADEMIC, 100))

    def test_59_percent_is_not_enough(self):
        self.assertIn("at least 60%", mark_error(Pathway.ACADEMIC, 59))

    def test_missing_mark_for_academic(self):
        self.assertIsNotNone(mark_error(Pathway.ACADEMIC, None))

    def test_out_of_range_mark(self):
        self.assertIsNotNone(mark_error(Pathway.ACADEMIC, 101))

    def test_teachers_do_not_need_matric_marks(self):
        self.assertIsNone(mark_error(Pathway.TEACHER, None))
        self.assertIsNone(mark_error(Pathway.TEACHER, 40))


class GradeRuleTests(SimpleTestCase):
    def test_valid_grades(self):
        self.assertIsNone(grades_error([8, 9, 10]))

    def test_empty_grades(self):
        self.assertIsNotNone(grades_error([]))

    def test_grade_out_of_range(self):
        self.assertIsNotNone(grades_error([7, 8]))
        self.assertIsNotNone(grades_error([13]))

    def test_duplicate_grades(self):
        self.assertIsNotNone(grades_error([10, 10]))


class SubmissionRuleTests(SimpleTestCase):
    def test_complete_academic_application(self):
        errors = submission_errors(
            pathway=Pathway.ACADEMIC, subjects=[(74, [10, 11, 12])],
            document_kinds={DocumentKind.ID_DOCUMENT, DocumentKind.MATRIC_RESULTS},
            sace_number="", qualification_name="",
        )
        self.assertEqual(errors, {})

    def test_academic_missing_documents_and_subjects(self):
        errors = submission_errors(
            pathway=Pathway.ACADEMIC, subjects=[], document_kinds={DocumentKind.ID_DOCUMENT},
            sace_number="", qualification_name="",
        )
        self.assertIn("subjects", errors)
        self.assertIn("documents", errors)

    def test_teacher_needs_sace_and_qualification(self):
        errors = submission_errors(
            pathway=Pathway.TEACHER, subjects=[(None, [8])],
            document_kinds={DocumentKind.ID_DOCUMENT, DocumentKind.TEACHING_QUALIFICATION,
                            DocumentKind.SACE_CERTIFICATE},
            sace_number="", qualification_name=" ",
        )
        self.assertEqual(set(errors), {"sace_number", "qualification_name"})
