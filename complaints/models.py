import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_tracking_id():
    return f"CP-{uuid.uuid4().hex[:10].upper()}"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
    ]

    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
    ]

    tracking_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="Medium")
    department = models.ForeignKey(
        "department_portal.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            while True:
                candidate = generate_tracking_id()
                if not Complaint.objects.filter(tracking_id=candidate).exclude(pk=self.pk).exists():
                    self.tracking_id = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tracking_id or str(self.pk)


class ComplaintUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return str(self.user)
