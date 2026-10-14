from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dept_dashboard"),
    path("login/<slug:slug>/", views.dept_login, name="dept_login"),
    path("logout/", views.dept_logout, name="dept_logout"),
    path("overview/", views.overview, name="dept_overview"),
    path("complaints/", views.complaint_list, name="dept_complaints"),
    path("complaints/<int:pk>/", views.work_progress, name="dept_work_progress"),
]
