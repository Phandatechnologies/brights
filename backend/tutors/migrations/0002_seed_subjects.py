"""
Seed the subject list with common National Senior Certificate (Grade 10–12) subjects.
Mathematics and the languages are also taught in Grades 8–9.
Admins can add, rename or deactivate subjects in the Django admin.
"""

from django.db import migrations

LANGUAGES = ["Afrikaans", "English", "isiNdebele", "isiXhosa", "isiZulu", "Sepedi",
             "Sesotho", "Setswana", "siSwati", "Tshivenda", "Xitsonga"]

OTHER_SUBJECTS = [
    "Accounting", "Agricultural Sciences", "Business Studies", "Civil Technology",
    "Computer Applications Technology", "Consumer Studies", "Dramatic Arts", "Economics",
    "Electrical Technology", "Engineering Graphics and Design", "Geography", "History",
    "Hospitality Studies", "Information Technology", "Life Sciences", "Mathematical Literacy",
    "Mathematics", "Mechanical Technology", "Music", "Physical Sciences", "Religion Studies",
    "Technical Mathematics", "Technical Sciences", "Tourism", "Visual Arts",
]


def subject_names():
    names = list(OTHER_SUBJECTS)
    for language in LANGUAGES:
        names.append(f"{language} Home Language")
        names.append(f"{language} First Additional Language")
    return names


def seed(apps, schema_editor):
    Subject = apps.get_model("tutors", "Subject")
    for name in subject_names():
        Subject.objects.get_or_create(name=name)


def unseed(apps, schema_editor):
    Subject = apps.get_model("tutors", "Subject")
    Subject.objects.filter(name__in=subject_names()).delete()


class Migration(migrations.Migration):
    dependencies = [("tutors", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
