"""
Seed general areas for the Gauteng launch. Admins can add, rename or
deactivate areas, and add other provinces when Brights expands.
"""

from django.db import migrations

GAUTENG_AREAS = [
    # City of Tshwane
    "Atteridgeville", "Centurion", "Ga-Rankuwa", "Hammanskraal", "Mabopane", "Mamelodi",
    "Pretoria Central", "Pretoria East", "Pretoria North", "Soshanguve",
    # City of Johannesburg
    "Alexandra", "Diepsloot", "Fourways", "Johannesburg CBD", "Johannesburg South",
    "Midrand", "Randburg", "Roodepoort", "Rosebank", "Sandton", "Soweto",
    # Ekurhuleni
    "Benoni", "Boksburg", "Brakpan", "Edenvale", "Germiston", "Kempton Park",
    "Katlehong", "Springs", "Tembisa", "Thokoza", "Vosloorus",
    # West Rand and Sedibeng
    "Krugersdorp", "Mogale City", "Randfontein", "Westonaria",
    "Vanderbijlpark", "Vereeniging", "Sebokeng", "Evaton", "Meyerton",
]


def seed(apps, schema_editor):
    Area = apps.get_model("profiles", "Area")
    for name in GAUTENG_AREAS:
        Area.objects.get_or_create(name=name, province="gauteng")


def unseed(apps, schema_editor):
    apps.get_model("profiles", "Area").objects.filter(province="gauteng", name__in=GAUTENG_AREAS).delete()


class Migration(migrations.Migration):
    dependencies = [("profiles", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
