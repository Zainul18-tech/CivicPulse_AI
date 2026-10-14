
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
    path("admin/complaints/", views.admin_complaints, name="admin_complaints"),
    path(
        "admin/duplicate-review/",
        views.admin_duplicate_review,
        name="admin_duplicate_review",
    ),
    path("admin/analytics/", views.admin_analytics, name="admin_analytics"),
    path("admin/officers/", views.admin_officers, name="admin_officers"),

    # Citizen complaint flow
    path("complaints/submit/", views.submit_complaint, name="submit_complaint"),
    path("complaints/", views.my_complaints, name="my_complaints"),
    path("complaints/<int:pk>/", views.complaint_detail, name="complaint_detail"),

    # Logout
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
]
