from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    Application,
    ApplicationField,
    WorkflowAction,
    WorkflowRequest,
    WorkflowTransition,
    WorkflowRequestFile,
    move_request,
)


@login_required
def application_list(request):
    applications = (
        Application.objects
        .filter(
            is_active=True,
            workflow__is_active=True,
        )
        .select_related("workflow")
        .prefetch_related("fields")
        .order_by("name")
    )

    return render(
        request,
        "workflows/application_list.html",
        {
            "applications": applications,
        },
    )


@login_required
def application_detail(request, application_id):
    application = get_object_or_404(
        Application.objects
        .select_related("workflow")
        .prefetch_related("fields"),
        id=application_id,
        is_active=True,
    )

    workflow = application.workflow

    if not workflow or not workflow.is_active:
        messages.error(
            request,
            "This application is currently unavailable.",
        )
        return redirect("workflows:application_list")

    fields = application.fields.all()

    if request.method == "POST":
        submitted_data = {}
        uploaded_files = []

        for field in fields:

            if field.field_type == ApplicationField.FieldType.FILE:
                value = request.FILES.get(field.name)

                if field.is_required and not value:
                    messages.error(
                        request,
                        f"{field.label} is required.",
                    )

                    return render(
                        request,
                        "workflows/application_detail.html",
                        {
                            "application": application,
                            "workflow": workflow,
                            "fields": fields,
                        },
                    )

                if value:
                    uploaded_files.append(
                        (field.name, value)
                    )

                continue

            if field.field_type == ApplicationField.FieldType.CHECKBOX:
                value = field.name in request.POST
            else:
                value = request.POST.get(
                    field.name,
                    "",
                ).strip()

            if field.is_required and value in ["", False]:
                messages.error(
                    request,
                    f"{field.label} is required.",
                )

                return render(
                    request,
                    "workflows/application_detail.html",
                    {
                        "application": application,
                        "workflow": workflow,
                        "fields": fields,
                    },
                )

            submitted_data[field.name] = value

        # The first ordered step is the first review stage.
        start_step = workflow.steps.order_by("order").first()

        if not start_step:
            messages.error(
                request,
                "This workflow does not have any review stages configured.",
            )
            return redirect("workflows:application_list")

        workflow_request = WorkflowRequest.objects.create(
            workflow=workflow,
            submitted_by=request.user,
            form_data=submitted_data,
            current_step=start_step,
            status=WorkflowRequest.Status.IN_PROGRESS,
        )

        for field_name, uploaded_file in uploaded_files:

            WorkflowRequestFile.objects.create(
                request=workflow_request,
                field_name=field_name,
                file=uploaded_file,
            )

        WorkflowAction.objects.create(
            request=workflow_request,
            performed_by=request.user,
            action=WorkflowAction.Action.SUBMIT,
            from_step=None,
            to_step=start_step,
        )

        messages.success(
            request,
            f"Application submitted successfully. "
            f"Request #{workflow_request.id}.",
        )

        return redirect(
            "workflows:request_detail",
            request_id=workflow_request.id,
        )

    return render(
        request,
        "workflows/application_detail.html",
        {
            "application": application,
            "workflow": workflow,
            "fields": fields,
        },
    )


@login_required
def request_detail(request, request_id):
    workflow_request = get_object_or_404(
        WorkflowRequest.objects
        .select_related(
            "workflow",
            "workflow__application",
            "submitted_by",
            "current_step",
        )
        .prefetch_related(
            "workflow__application__fields",
            "current_step__transitions",
            "actions__performed_by",
            "actions__from_step",
            "actions__to_step",
            "files",
        ),
        id=request_id,
    )

    is_owner = request.user == workflow_request.submitted_by
    is_admin = request.user.role == request.user.Role.ADMIN

    is_current_reviewer = (
        workflow_request.current_step is not None
        and request.user.role
        == workflow_request.current_step.assigned_role
    )

    if not (is_owner or is_current_reviewer or is_admin):
        raise PermissionDenied

    field_map = {
        field.name: field.label
        for field in workflow_request.workflow.application.fields.all()
    }

    file_field_map = {
        field.name: field.label
        for field in workflow_request.workflow.application.fields.all()
    }

    return render(
        request,
        "workflows/request_detail.html",
        {
            "workflow_request": workflow_request,
            "field_map": field_map,
            "file_field_map": file_field_map,
        },
    )


@login_required
def execute_transition(request, request_id, transition_id):
    if request.method != "POST":
        return redirect(
            "workflows:request_detail",
            request_id=request_id,
        )

    workflow_request = get_object_or_404(
        WorkflowRequest.objects.select_related(
            "current_step",
        ),
        id=request_id,
    )

    transition = get_object_or_404(
        WorkflowTransition.objects.select_related(
            "step",
            "target_step",
        ),
        id=transition_id,
    )

    current_step = workflow_request.current_step

    if workflow_request.is_finished:
        messages.error(
            request,
            "This request has already been completed.",
        )
        return redirect(
            "workflows:request_detail",
            request_id=request_id,
        )

    if current_step is None:
        messages.error(
            request,
            "This request does not have an active review stage.",
        )
        return redirect(
            "workflows:request_detail",
            request_id=request_id,
        )

    if current_step != transition.step:
        messages.error(
            request,
            "This transition is no longer available.",
        )
        return redirect(
            "workflows:request_detail",
            request_id=request_id,
        )

    if (
        request.user.role != current_step.assigned_role
        and request.user.role != request.user.Role.ADMIN
    ):
        raise PermissionDenied

    comment = request.POST.get(
        "comment",
        "",
    ).strip()

    try:
        move_request(
            workflow_request=workflow_request,
            transition=transition,
            user=request.user,
            comment=comment,
        )

        if workflow_request.current_step:
            destination = (
                workflow_request.current_step.name
            )
            messages.success(
                request,
                f"Request #{workflow_request.id} moved to "
                f"{destination}.",
            )
        else:
            messages.success(
                request,
                f"Request #{workflow_request.id} is now "
                f"{workflow_request.get_status_display()}.",
            )

    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

    return redirect(
        "workflows:request_detail",
        request_id=request_id,
    )


@login_required
def approval_dashboard(request):
    if request.user.role not in [
        request.user.Role.FACULTY,
        request.user.Role.HOD,
        request.user.Role.HOS,
        request.user.Role.ADMIN,
    ]:
        raise PermissionDenied

    pending_requests = (
        WorkflowRequest.objects
        .filter(
            status=WorkflowRequest.Status.IN_PROGRESS,
            current_step__assigned_role=request.user.role,
        )
        .select_related(
            "workflow",
            "workflow__application",
            "submitted_by",
            "current_step",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "workflows/approval_dashboard.html",
        {
            "pending_requests": pending_requests,
        },
    )

@login_required
def resubmit_request(request, request_id):
    workflow_request = get_object_or_404(
        WorkflowRequest.objects.select_related(
            "workflow",
            "workflow__application",
            "submitted_by",
            "return_step",
        ).prefetch_related(
            "workflow__application__fields",
            "files",
        ),
        id=request_id,
    )

    # Only the student who submitted the request can resubmit it.
    if request.user != workflow_request.submitted_by:
        raise PermissionDenied

    if workflow_request.status != WorkflowRequest.Status.CHANGES_REQUESTED:
        messages.error(
            request,
            "This application is not waiting for changes.",
        )
        return redirect(
            "workflows:request_detail",
            request_id=request_id,
        )

    if workflow_request.return_step is None:
        messages.error(
            request,
            "No review stage was saved for this resubmission.",
        )
        return redirect(
            "workflows:request_detail",
            request_id=request_id,
        )

    fields = workflow_request.workflow.application.fields.all()

    if request.method == "POST":
        submitted_data = {}
        uploaded_files = []

        for field in fields:

            if field.field_type == ApplicationField.FieldType.FILE:
                value = request.FILES.get(field.name)

                # If a new file wasn't uploaded, keep the existing file.
                if value:
                    uploaded_files.append(
                        (field.name, value)
                    )

                elif field.is_required:
                    existing_file = workflow_request.files.filter(
                        field_name=field.name
                    ).first()

                    if not existing_file:
                        messages.error(
                            request,
                            f"{field.label} is required.",
                        )

                        return render(
                            request,
                            "workflows/resubmit_request.html",
                            {
                                "workflow_request": workflow_request,
                                "fields": fields,
                            },
                        )

                continue

            if field.field_type == ApplicationField.FieldType.CHECKBOX:
                value = field.name in request.POST
            else:
                value = request.POST.get(
                    field.name,
                    "",
                ).strip()

            if field.is_required and value in ["", False]:
                messages.error(
                    request,
                    f"{field.label} is required.",
                )

                return render(
                    request,
                    "workflows/resubmit_request.html",
                    {
                        "workflow_request": workflow_request,
                        "fields": fields,
                    },
                )

            submitted_data[field.name] = value

        # Replace submitted form data.
        workflow_request.form_data = submitted_data

        # Return to the reviewer who requested changes.
        workflow_request.current_step = workflow_request.return_step

        workflow_request.return_step = None

        workflow_request.status = WorkflowRequest.Status.IN_PROGRESS

        workflow_request.save(
            update_fields=[
                "form_data",
                "current_step",
                "return_step",
                "status",
                "updated_at",
            ]
        )

        # Save newly uploaded files.
        for field_name, uploaded_file in uploaded_files:
            # Remove the previous file for this field.
            workflow_request.files.filter(
                field_name=field_name
            ).delete()

            WorkflowRequestFile.objects.create(
                request=workflow_request,
                field_name=field_name,
                file=uploaded_file,
            )

        # Record the resubmission in the workflow history.
        WorkflowAction.objects.create(
            request=workflow_request,
            performed_by=request.user,
            action=WorkflowAction.Action.SUBMIT,
            from_step=None,
            to_step=workflow_request.current_step,
            comment="Application resubmitted after requested changes.",
        )

        messages.success(
            request,
            f"Application resubmitted successfully. "
            f"Request #{workflow_request.id} is back under review.",
        )

        return redirect(
            "workflows:request_detail",
            request_id=workflow_request.id,
        )

    return render(
        request,
        "workflows/resubmit_request.html",
        {
            "workflow_request": workflow_request,
            "fields": fields,
        },
    )

