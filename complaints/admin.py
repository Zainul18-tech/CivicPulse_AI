
from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_id",
        "title",
        "citizen",
        "category",
        "priority",
        "status",
        "department",
        "created_at",
    )

    list_filter = (
        "category",
        "priority",
        "status",
        "department",
    )

    search_fields = (
        "tracking_id",
        "title",
        "description",
        "citizen__username",
    )

    readonly_fields = (
        "tracking_id",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)
