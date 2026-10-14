from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from complaints.models import Complaint
from .models import (
    Department,
    DepartmentProfile,
    DepartmentTeam,
    WorkRecord,
    WorkUpdate,
)

STATUS_CHOICES = ["Pending", "In Progress", "Resolved"]
PRIORITY_CHOICES = ["High", "Medium", "Low"]
DEPARTMENT_ICONS = {
    "roads-public-infrastructure": "🛣️",
    "water-supply": "💧",
    "sanitation-solid-waste": "♻️",
    "electrical-streetlight": "💡",
    "drainage-flood-management": "🌧️",
}
department_staff_required = user_passes_test(
    lambda user: (
        user.is_authenticated
        and user.is_staff
        and DepartmentProfile.objects.filter(user=user).exists()
    ),
    login_url="dept_dashboard",
)


def dept_complaints(department):
    return Complaint.objects.filter(department=department)


def current_dept(request):
    profile = getattr(request.user, "departmentprofile", None)
    if profile is None:
        return None
    return profile.department


def dashboard(request):
    data = []
    for department in Department.objects.order_by("name"):
        open_count = dept_complaints(department).exclude(status="Resolved").count()
        data.append(
            {
                "dept": department,
                "open_count": open_count,
                "icon": DEPARTMENT_ICONS.get(department.slug, "🏛️"),
            }
        )
    return render(request, "department/dashboard.html", {"data": data})


def dept_login(request, slug):
    department = get_object_or_404(Department, slug=slug)
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        profile = getattr(user, "departmentprofile", None) if user else None
        if user is not None and user.is_staff and profile and profile.department == department:
            login(request, user)
            return redirect("dept_overview")
        messages.error(request, "Invalid username or credentials.")
    return render(request, "department/login.html", {"department": department})


def dept_logout(request):
    logout(request)
    return redirect("dept_dashboard")


@department_staff_required
def overview(request):
    department = current_dept(request)
    if department is None:
        return redirect("dept_dashboard")

    complaints = dept_complaints(department)
    today = timezone.localdate()
    overdue_records = WorkRecord.objects.filter(
        complaint__in=complaints,
        deadline__lt=today,
    )
    overdue = (
        overdue_records
        .exclude(complaint__status="Resolved")
        .count()
    )
    priority_counts = dict(
        complaints.values("priority")
        .annotate(count=Count("id"))
        .values_list("priority", "count")
    )
    total = complaints.count()
    priority = [
        {
            "name": level,
            "count": priority_counts.get(level, 0),
            "percentage": round(priority_counts.get(level, 0) * 100 / total)
            if total
            else 0,
        }
        for level in PRIORITY_CHOICES
    ]
    activity = [
        {
            "kind": "update",
            "complaint": update.complaint,
            "description": update.work_done,
            "status": update.status,
            "date": update.created_at,
            "user": update.updated_by,
        }
        for update in WorkUpdate.objects.filter(complaint__in=complaints)
        .select_related("complaint", "updated_by")[:10]
    ]
    activity.extend(
        {
            "kind": "new",
            "complaint": complaint,
            "description": "New complaint received",
            "status": complaint.status,
            "date": complaint.created_at,
            "user": complaint.user,
        }
        for complaint in complaints.select_related("user")[:10]
    )
    activity.sort(key=lambda item: item["date"], reverse=True)
    context = {
        "department": department,
        "total": total,
        "pending": complaints.filter(status="Pending").count(),
        "in_progress": complaints.filter(status="In Progress").count(),
        "resolved": complaints.filter(status="Resolved").count(),
        "overdue": overdue,
        "priority": priority,
        "activity": activity[:10],
    }
    return render(request, "department/overview.html", context)


@department_staff_required
def complaint_list(request):
    department = current_dept(request)
    if department is None:
        return redirect("dept_dashboard")

    complaints = (
        dept_complaints(department)
        .select_related(
            "department",
            "work",
            "work__assigned_user",
            "work__assigned_team",
        )
        .prefetch_related(
            Prefetch(
                "work_updates",
                queryset=WorkUpdate.objects.order_by("-created_at"),
                to_attr="ordered_work_updates",
            )
        )
    )
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    if query:
        search = (
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(tracking_id__icontains=query)
            | Q(work__assigned_staff__icontains=query)
        )
        if query.isdigit():
            search |= Q(pk=int(query))
        complaints = complaints.filter(search)
    if status:
        if status == "Overdue":
            complaints = complaints.filter(
                work__deadline__lt=timezone.localdate()
            ).exclude(status="Resolved")
        elif status in STATUS_CHOICES:
            complaints = complaints.filter(status=status)
    if priority:
        if priority in PRIORITY_CHOICES:
            complaints = complaints.filter(priority=priority)

    ordering = request.GET.get("sort", "deadline")
    if ordering == "-deadline":
        complaints = complaints.order_by("-work__deadline", "-created_at")
    elif ordering == "newest":
        complaints = complaints.order_by("-created_at")
    else:
        ordering = "deadline"
        complaints = complaints.order_by("work__deadline", "-created_at")

    return render(
        request,
        "department/complaint_list.html",
        {
            "complaints": complaints.order_by("pk"),
            "q": query,
            "status": status,
            "priority": priority,
            "sort": ordering,
            "priorities": PRIORITY_CHOICES,
            "statuses": [*STATUS_CHOICES, "Overdue"],
            "today": timezone.localdate(),
            "department": department,
        },
    )


@department_staff_required
def work_progress(request, pk):
    department = current_dept(request)
    if department is None:
        return redirect("dept_dashboard")
    complaint = get_object_or_404(dept_complaints(department), pk=pk)
    work, _ = WorkRecord.objects.get_or_create(complaint=complaint)
    staff_members = User.objects.filter(
        is_staff=True,
        departmentprofile__department=department,
    ).order_by("first_name", "last_name", "username")
    teams = DepartmentTeam.objects.filter(department=department)

    if request.method == "POST":
        assignee = request.POST.get("assignee", "")
        assigned_user = None
        assigned_team = None
        if assignee.startswith("staff:"):
            assigned_user = staff_members.filter(pk=assignee[6:]).first()
            if assigned_user is None:
                messages.error(request, "Select a valid staff member for this department.")
                return redirect("dept_work_progress", pk=pk)
        elif assignee.startswith("team:"):
            assigned_team = teams.filter(pk=assignee[5:]).first()
            if assigned_team is None:
                messages.error(request, "Select a valid team for this department.")
                return redirect("dept_work_progress", pk=pk)
        elif assignee:
            messages.error(request, "Select a valid staff member or team.")
            return redirect("dept_work_progress", pk=pk)

        deadline_value = request.POST.get("deadline", "").strip()
        try:
            deadline = date.fromisoformat(deadline_value) if deadline_value else None
        except ValueError:
            messages.error(request, "Enter a valid deadline.")
            return redirect("dept_work_progress", pk=pk)

        new_status = request.POST.get("status", complaint.status)
        if request.POST.get("action") == "resolve":
            new_status = "Resolved"
        if new_status not in STATUS_CHOICES:
            messages.error(request, "Select a valid complaint status.")
            return redirect("dept_work_progress", pk=pk)
        status_changed = new_status != complaint.status

        work_done = request.POST.get("work_done", "").strip()
        work_date_value = request.POST.get("work_date", "").strip()
        has_update = bool(
            work_done
            or request.FILES.get("before_photo")
            or request.FILES.get("after_photo")
            or request.FILES.get("photo")
            or status_changed
        )
        try:
            work_date = date.fromisoformat(work_date_value) if work_date_value else timezone.localdate()
        except ValueError:
            messages.error(request, "Enter a valid work date.")
            return redirect("dept_work_progress", pk=pk)

        work.assigned_user = assigned_user
        work.assigned_team = assigned_team
        work.assigned_staff = (
            assigned_user.get_full_name() or assigned_user.username
            if assigned_user
            else assigned_team.name if assigned_team else ""
        )
        work.deadline = deadline
        if work_done:
            work.work_notes = work_done
        work.save()

        if status_changed:
            complaint.status = new_status
            complaint.updated_at = timezone.now()
            complaint.save(update_fields=["status", "updated_at"])

        if has_update:
            WorkUpdate.objects.create(
                complaint=complaint,
                work_done=work_done or "Complaint status updated.",
                work_date=work_date,
                status=new_status if status_changed else "",
                updated_by=request.user,
                photo=request.FILES.get("photo"),
                before_photo=request.FILES.get("before_photo"),
                after_photo=request.FILES.get("after_photo"),
            )
        messages.success(request, "Update saved.")
        return redirect("dept_work_progress", pk=pk)

    return render(
        request,
        "department/work_progress.html",
        {
            "c": complaint,
            "work": work,
            "statuses": STATUS_CHOICES,
            "today": timezone.localdate().isoformat(),
            "department": department,
            "staff_members": staff_members,
            "teams": teams,
            "updates": complaint.work_updates.select_related("updated_by").all(),
        },
    )
