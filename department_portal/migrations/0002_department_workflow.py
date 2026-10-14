import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


DEPARTMENTS = [
    ("Roads and Public Infrastructure", "roads-public-infrastructure"),
    ("Water Supply", "water-supply"),
    ("Sanitation and Solid Waste Management", "sanitation-solid-waste"),
    ("Electrical and Streetlight Maintenance", "electrical-streetlight"),
    ("Drainage and Flood Management", "drainage-flood-management"),
]


def create_default_departments(apps, schema_editor):
    Department = apps.get_model("department_portal", "Department")
    for name, slug in DEPARTMENTS:
        Department.objects.get_or_create(name=name, defaults={"slug": slug})


class Migration(migrations.Migration):
    dependencies = [
        ("department_portal", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DepartmentTeam",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="teams",
                        to="department_portal.department",
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="departmentteam",
            constraint=models.UniqueConstraint(
                fields=("department", "name"),
                name="unique_department_team_name",
            ),
        ),
        migrations.AddField(
            model_name="workrecord",
            name="assigned_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="department_work_assignments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="workrecord",
            name="assigned_team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="work_records",
                to="department_portal.departmentteam",
            ),
        ),
        migrations.AddField(
            model_name="workupdate",
            name="after_photo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="completion_photos/after/",
            ),
        ),
        migrations.AddField(
            model_name="workupdate",
            name="before_photo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="completion_photos/before/",
            ),
        ),
        migrations.AddField(
            model_name="workupdate",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Pending", "Pending"),
                    ("In Progress", "In Progress"),
                    ("Resolved", "Resolved"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="workupdate",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="department_work_updates",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(create_default_departments, migrations.RunPython.noop),
    ]
