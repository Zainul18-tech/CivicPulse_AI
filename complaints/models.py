
import uuid

from django.conf import settings
from django.db import models


def generate_tracking_id():
    return f"CP-{uuid.uuid4().hex[:10].upper()}"


class Complaint(models.Model):

    class Category(models.TextChoices):
        ROADS = "ROADS", "Roads and Public Infrastructure"
        WATER = "WATER", "Water Supply"
        SANITATION = "SANITATION", "Sanitation and Solid Waste"
        ELECTRICAL = "ELECTRICAL", "Electrical and Streetlights"
        DRAINAGE = "DRAINAGE", "Drainage and Flood Management"
        OTHER = "OTHER", "Other / Unclassified"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        ANALYZING = "ANALYZING", "Analyzing"
        ASSIGNED = "ASSIGNED", "Assigned"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"
        REJECTED = "REJECTED", "Rejected"

    # Unique complaint tracking ID
    tracking_id = models.CharField(
        max_length=13,
        unique=True,
        default=generate_tracking_id,
        editable=False,
    )

    # Citizen who submitted the complaint
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="civic_complaints",
    )

    # Complaint details
    title = models.CharField(max_length=150)
    description = models.TextField()

    # Category assigned by the system or staff
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )

    # System-assessed priority
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    # Priority selected by the citizen
    citizen_priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    # Complaint workflow status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )

    # Language used to submit the complaint
    language = models.CharField(
        max_length=20,
        default="English",
    )

    # Manually entered location or GPS-derived location
    location = models.CharField(max_length=255)

    # GPS coordinates
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    # Uploaded supporting image
    evidence_image = models.ImageField(
        upload_to="complaint_evidence/",
        null=True,
        blank=True,
    )

    # Photo captured using the device camera
    live_image = models.ImageField(
        upload_to="complaint_live_photos/",
        null=True,
        blank=True,
    )

    # Department handling the complaint
    department = models.CharField(
        max_length=100,
        blank=True,
    )

    # Staff member assigned to the complaint
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_civic_complaints",
    )

    # Service-level agreement deadline
    sla_deadline = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Staff resolution notes
    resolution_notes = models.TextField(blank=True)

    # Links a possible duplicate to its original complaint
    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_complaints",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["category", "priority"]),
            models.Index(fields=["department", "status"]),
        ]

    def __str__(self):
        return f"{self.tracking_id} - {self.title}"
