
from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path("", views.home, name="home"),

    # Citizen authentication
    path(
        "citizen/signup/",
        views.citizen_signup,
        name="citizen_signup",
    ),
    path(
        "citizen/login/",
        views.citizen_login,
        name="citizen_login",
    ),

    # Staff authentication
    path(
        "admin/login/",
        views.admin_login,
        name="admin_login",
    ),

    # Staff account creation (superuser only)
    path(
        "admin/staff/create/",
        views.create_staff_account,
        name="create_staff_account",
    ),

    # Dashboards
    path(
        "citizen/dashboard/",
        views.citizen_dashboard,
        name="dashboard",
    ),
    path(
        "admin/dashboard/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),

    path(
    "citizen/complaints/submit/",
    views.submit_complaint,
    name="submit_complaint",
    ),
    
    path(
    "citizen/complaints/",
    views.my_complaints,
    name="my_complaints",
    ),

    # Logout
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
]
