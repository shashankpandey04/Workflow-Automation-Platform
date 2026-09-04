from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "dashboard/student/",
        views.student_dashboard,
        name="student_dashboard",
    ),

    path(
        "dashboard/faculty/",
        views.faculty_dashboard,
        name="faculty_dashboard",
    ),

    path(
        "dashboard/hod/",
        views.hod_dashboard,
        name="hod_dashboard",
    ),

    path(
        "dashboard/hos/",
        views.hos_dashboard,
        name="hos_dashboard",
    ),

    path(
        "dashboard/admin/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
]