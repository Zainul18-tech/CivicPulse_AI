
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import (
    CitizenSignUpForm,
    StaffCreationForm,
    ComplaintSubmissionForm,
)
from .models import Complaint


def home(request):
    """Public CivicPulse AI homepage."""
    return render(request, "home.html")


def citizen_signup(request):
    """Register a new citizen account."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_dashboard")
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


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="admin_login",
)
def admin_dashboard(request):
    """Display the staff dashboard."""
    return render(request, "admin/dashboard.html")



@login_required(login_url="citizen_login")
def submit_complaint(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")

    if request.method == "POST":
        form = ComplaintSubmissionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user

            # Keep system-assessed priority separate from citizen priority.
            complaint.priority = Complaint.Priority.MEDIUM

            complaint.save()

            messages.success(
                request,
                f"Complaint submitted successfully. "
                f"Your tracking ID is {complaint.tracking_id}.",
            )
            return redirect("my_complaints")

        messages.error(
            request,
            "Please correct the errors below and submit again.",
        )
    else:
        form = ComplaintSubmissionForm()

    return render(
        request,
        "citizen/submit_complaint.html",
        {"form": form},
    )



@login_required(login_url="citizen_login")
def my_complaints(request):
    """Show only complaints submitted by the logged-in citizen."""
    if request.user.is_staff:
        return redirect("admin_dashboard")

    complaints = Complaint.objects.filter(
        citizen=request.user
    ).order_by("-created_at")

    return render(
        request,
        "citizen/my_complaints.html",
        {"complaints": complaints},
    )


@user_passes_test(
    lambda user: user.is_authenticated and user.is_superuser,
    login_url="admin_login",
)
def create_staff_account(request):
    """Allow only superusers to create staff accounts."""
    if request.method == "POST":
        form = StaffCreationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Staff account created successfully.",
            )
            return redirect("create_staff_account")
    else:
        form = StaffCreationForm()

    return render(
        request,
        "admin/create_staff_account.html",
        {"form": form},
    )


@require_POST
def logout_view(request):
    """Log out and redirect to citizen login."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("citizen_login")
