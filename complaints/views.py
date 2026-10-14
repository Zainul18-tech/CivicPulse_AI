
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from department_portal.models import Department
from .forms import CitizenSignUpForm, StaffCreationForm
from .models import Complaint


def home(request):
    """Public CivicPulse AI homepage."""
    return render(request, "home.html")


def citizen_signup(request):
    """Register a new citizen account."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = CitizenSignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Your citizen account has been created successfully.",
            )
            return redirect("dashboard")
    else:
        form = CitizenSignUpForm()

    return render(
        request,
        "accounts/citizen_signup.html",
        {"form": form},
    )


def citizen_login(request):
    """Authenticate citizens without granting staff access."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_dashboard")
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None and not user.is_staff:
            login(request, user)
            return redirect("dashboard")

        messages.error(
            request,
            "Invalid citizen credentials. Please check and try again.",
        )

    return render(request, "accounts/citizen_login.html")


def admin_login(request):
    """Authenticate only authorized staff accounts."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_dashboard")

        messages.error(
            request,
            "Your account does not have staff access.",
        )
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None and user.is_staff:
            login(request, user)
            return redirect("admin_dashboard")

        messages.error(
            request,
            "Invalid staff credentials or insufficient permissions.",
        )

    return render(request, "accounts/admin_login.html")


@login_required(login_url="citizen_login")
def citizen_dashboard(request):
    """Display the citizen dashboard to authenticated citizens."""
    if request.user.is_staff:
        return redirect("admin_dashboard")

    return render(request, "citizen/dashboard.html")


@login_required(login_url="citizen_login")
def submit_complaint(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = (request.POST.get("description") or "").strip()
        priority = request.POST.get("priority", "Medium")
        department_id = request.POST.get("department")

        department = None
        if department_id:
            department = Department.objects.filter(pk=department_id).first()

        if (
            title
            and description
            and priority in dict(Complaint.PRIORITY_CHOICES)
            and (not department_id or department is not None)
        ):
            complaint = Complaint.objects.create(
                user=request.user,
                title=title,
                description=description,
                priority=priority,
                department=department,
            )
            messages.success(request, "Your complaint has been submitted successfully.")
            return redirect("complaint_detail", pk=complaint.pk)
        messages.error(
            request,
            "Provide a title and description, and choose a valid priority and department.",
        )

    return render(
        request,
        "citizen/submit_complaint.html",
        {"departments": Department.objects.all()},
    )


@login_required(login_url="citizen_login")
def my_complaints(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    complaints = (
        Complaint.objects.filter(user=request.user)
        .select_related("department")
        .order_by("-created_at")
    )
    return render(request, "citizen/my_complaints.html", {"complaints": complaints})


@login_required(login_url="citizen_login")
def complaint_detail(request, pk):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    complaint = get_object_or_404(Complaint, pk=pk, user=request.user)
    updates = complaint.work_updates.all().order_by("-created_at")
    return render(
        request,
        "citizen/complaint_detail.html",
        {"complaint": complaint, "updates": updates},
    )


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/",
)
def admin_dashboard(request):
    context = {
        "total_complaints": Complaint.objects.count(),
        "open_complaints": Complaint.objects.exclude(status="Resolved").count(),
        "staff_count": User.objects.filter(is_staff=True).count(),
    }
    return render(request, "admin/dashboard.html", context)


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/",
)
def admin_complaints(request):
    complaints = Complaint.objects.select_related("user", "department").order_by("-created_at")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    department_id = request.GET.get("department", "")

    if request.method == "POST":
        complaint = get_object_or_404(Complaint, pk=request.POST.get("complaint_id"))
        department_id = request.POST.get("department", "")
        if department_id:
            department = Department.objects.filter(pk=department_id).first()
            if department is None:
                messages.error(request, "Choose a valid department.")
                return redirect("admin_complaints")
        else:
            department = None
        complaint.department = department
        complaint.save(update_fields=["department"])
        messages.success(request, "Complaint department assignment updated.")
        return redirect("admin_complaints")

    if query:
        complaints = complaints.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(tracking_id__icontains=query)
        )
    if status:
        complaints = complaints.filter(status=status)
    if department_id:
        complaints = complaints.filter(department_id=department_id)
    return render(
        request,
        "admin/complaints.html",
        {
            "complaints": complaints,
            "query": query,
            "status": status,
            "department_filter": department_id,
            "departments": Department.objects.all(),
        },
    )


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/",
)
def admin_duplicate_review(request):
    duplicate_groups = (
        Complaint.objects.filter(title__isnull=False)
        .exclude(title="")
        .values("title")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
        .order_by("-count", "title")
    )
    flagged = []
    for group in duplicate_groups:
        flagged.extend(
            Complaint.objects.filter(title=group["title"])
            .select_related("user", "department")[:5]
        )
    return render(
        request,
        "admin/duplicate_review.html",
        {"duplicate_groups": duplicate_groups, "flagged": flagged},
    )


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/",
)
def admin_analytics(request):
    complaints = Complaint.objects.all()
    status_breakdown = list(
        complaints.values("status").annotate(total=Count("id")).order_by("status")
    )
    priority_breakdown = list(
        complaints.values("priority").annotate(total=Count("id")).order_by("priority")
    )
    departments = list(
        complaints.exclude(department__isnull=True)
        .values("department__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return render(
        request,
        "admin/analytics.html",
        {
            "status_breakdown": status_breakdown,
            "priority_breakdown": priority_breakdown,
            "departments": departments,
            "total_complaints": complaints.count(),
        },
    )


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/",
)
def admin_officers(request):
    officers = []
    for user in User.objects.filter(is_staff=True).order_by(
        "first_name", "last_name", "username"
    ):
        profile = getattr(user, "departmentprofile", None)
        officers.append(
            {"user": user, "department": profile.department if profile else None}
        )
    return render(request, "admin/officers.html", {"officers": officers})



@require_POST
def logout_view(request):
    """Log out and redirect to citizen login."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("citizen_login")


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="admin_login",
)
def create_staff_account(request):
    if request.method == "POST":
        form = StaffCreationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Staff account created successfully.")
            return redirect("create_staff_account")
    else:
        form = StaffCreationForm()

    return render(
        request,
        "admin/create_staff_account.html",
        {"form": form},
    )
