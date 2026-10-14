from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class DepartmentProfile(models.Model):
    """Links one login account to one department."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.department}"


class DepartmentTeam(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="teams",
    )
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_department_team_name",
            ),
        ]

    def __str__(self):
        return f"{self.department}: {self.name}"


class WorkRecord(models.Model):
    """Extra fields per complaint: staff and deadline."""

    complaint = models.OneToOneField(
        "complaints.Complaint",
        on_delete=models.CASCADE,
        related_name="work",
    )
    assigned_staff = models.CharField(max_length=100, blank=True)
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_work_assignments",
    )
    assigned_team = models.ForeignKey(
        DepartmentTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="work_records",
    )
    deadline = models.DateField(null=True, blank=True)
    work_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Work record for complaint {self.complaint_id}"


class WorkUpdate(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
    ]

    complaint = models.ForeignKey(
        "complaints.Complaint",
        on_delete=models.CASCADE,
        related_name="work_updates",
    )
    work_done = models.TextField()
    work_date = models.DateField()
    photo = models.ImageField(upload_to="completion_photos/", blank=True, null=True)
    before_photo = models.ImageField(
        upload_to="completion_photos/before/",
        blank=True,
        null=True,
    )
    after_photo = models.ImageField(
        upload_to="completion_photos/after/",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_work_updates",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Update for complaint {self.complaint_id}"
