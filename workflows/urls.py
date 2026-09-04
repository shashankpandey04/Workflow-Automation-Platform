from django.urls import path

from . import views


app_name = "workflows"


urlpatterns = [
    path(
        "",
        views.application_list,
        name="application_list",
    ),

    path(
        "applications/<int:application_id>/",
        views.application_detail,
        name="application_detail",
    ),

    path(
        "approvals/",
        views.approval_dashboard,
        name="approval_dashboard",
    ),

    path(
        "requests/<int:request_id>/",
        views.request_detail,
        name="request_detail",
    ),

    path(
        "requests/<int:request_id>/transition/<int:transition_id>/",
        views.execute_transition,
        name="execute_transition",
    ),

    path(
        "requests/<int:request_id>/resubmit/",
        views.resubmit_request,
        name="resubmit_request",
    ),
]