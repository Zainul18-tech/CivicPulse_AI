
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import CitizenSignUpForm, StaffCreationForm


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


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/",
)
def admin_dashboard(request):
    """Temporary landing page for authorized staff."""
    return render(request, "admin/dashboard.html")



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
            messages.success(
                request,
                "Staff account created successfully."
            )
            return redirect("create_staff_account")
    else:
        form = StaffCreationForm()

    return render(
        request,
        "admin/create_staff_account.html",
        {"form": form},
    )
