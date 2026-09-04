from django.conf import settings
from django.db import models

class Application(models.Model):
    """
    Defines WHAT a student/user can apply for.

    Example:
        - RPL Application
        - Internship Approval
        - Project Approval
        - Leave Request

    Application = what is being requested.
    Workflow = how the request gets processed.
    """

    class Category(models.TextChoices):
        ACADEMIC = "ACADEMIC", "Academic"
        ADMINISTRATIVE = "ADMINISTRATIVE", "Administrative"
        CAREER = "CAREER", "Career"
        FINANCIAL = "FINANCIAL", "Financial"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=200)

    description = models.TextField()

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
    )

    instructions = models.TextField(
        blank=True,
        help_text="Instructions shown to applicants.",
    )

    requirements = models.TextField(
        blank=True,
        help_text="Requirements shown to applicants.",
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_applications",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ApplicationField(models.Model):
    """
    Defines a field that an applicant must fill
    when submitting an Application.

    Example:
        Course Code      → TEXT
        Completion Date  → DATE
        Description      → TEXTAREA
        Supporting Docs  → FILE
    """

    class FieldType(models.TextChoices):
        TEXT = "TEXT", "Text"
        TEXTAREA = "TEXTAREA", "Long Text"
        NUMBER = "NUMBER", "Number"
        DATE = "DATE", "Date"
        URL = "URL", "URL"
        SELECT = "SELECT", "Dropdown"
        FILE = "FILE", "File Upload"
        CHECKBOX = "CHECKBOX", "Checkbox"

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="fields",
    )

    name = models.CharField(
        max_length=100,
        help_text="Internal field name. Example: course_code",
    )

    label = models.CharField(
        max_length=200,
        help_text="Label shown to the applicant.",
    )

    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
    )

    help_text = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional explanation shown below the field.",
    )

    placeholder = models.CharField(
        max_length=200,
        blank=True,
    )

    is_required = models.BooleanField(
        default=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    options = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'For dropdowns. Example: '
            '["Option 1", "Option 2", "Option 3"]'
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["application", "name"],
                name="unique_application_field_name",
            )
        ]

    def __str__(self):
        return f"{self.application.name} → {self.label}"

class ApplicationEligibilityRule(models.Model):
    class Field(models.TextChoices):
        ROLE = "ROLE", "Role"
        DEPARTMENT = "DEPARTMENT", "Department"
        PROGRAM = "PROGRAM", "Program"
        YEAR = "YEAR", "Year"
        SEMESTER = "SEMESTER", "Semester"
        BATCH = "BATCH", "Batch"

    class Operator(models.TextChoices):
        EQUALS = "EQUALS", "Equals"
        NOT_EQUALS = "NOT_EQUALS", "Not Equals"
        IN = "IN", "Is One Of"
        NOT_IN = "NOT_IN", "Is Not One Of"

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="eligibility_rules",
    )

    field = models.CharField(
        max_length=30,
        choices=Field.choices,
    )

    operator = models.CharField(
        max_length=20,
        choices=Operator.choices,
        default=Operator.EQUALS,
    )

    value = models.CharField(
        max_length=255,
        help_text=(
            "For IN/NOT IN, enter comma-separated values."
        ),
    )

    class Meta:
        ordering = ["field"]

    def __str__(self):
        return (
            f"{self.application.name}: "
            f"{self.get_field_display()} "
            f"{self.get_operator_display()} "
            f"{self.value}"
        )


class Workflow(models.Model):
    """
    Defines HOW an application is processed.

    Application = what the user wants.
    Workflow = how the request moves through approvals.
    """

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="workflow",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_workflows",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

class WorkflowStep(models.Model):
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="steps",
    )

    name = models.CharField(
        max_length=200,
        help_text="Name of the review stage.",
    )

    description = models.TextField(
        blank=True,
    )

    assigned_role = models.CharField(
        max_length=50,
        choices=[
            ("FACULTY", "Faculty"),
            ("HOD", "Head of Department"),
            ("HOS", "Head of School"),
            ("ADMIN", "Administrator"),
        ],
    )

    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "order"],
                name="unique_step_order_per_workflow",
            )
        ]

    def __str__(self):
        return f"{self.workflow.name} → {self.name}"


class WorkflowTransition(models.Model):
    class Action(models.TextChoices):
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"
        REQUEST_CHANGES = "REQUEST_CHANGES", "Request Changes"

    step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="transitions",
    )

    name = models.CharField(
        max_length=150,
        help_text="Human-readable business action.",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )

    target_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="incoming_transitions",
        null=True,
        blank=True,
        help_text=(
            "Leave empty when this action ends the workflow "
            "or returns the request to the applicant."
        ),
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        if self.target_step:
            return (
                f"{self.step.name} → "
                f"{self.name} → "
                f"{self.target_step.name}"
            )

        return f"{self.step.name} → {self.name}"

class WorkflowRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.PROTECT,
        related_name="requests",
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="workflow_requests",
    )

    form_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Submitted application form data.",
    )

    current_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        related_name="current_requests",
        null=True,
        blank=True,
    )

    return_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        related_name="returned_requests",
        null=True,
        blank=True,
        help_text=(
            "Review stage to return to when the applicant "
            "resubmits after changes are requested."
        ),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request #{self.id} - {self.workflow.name}"

    @property
    def is_finished(self):
        return self.status in [
            self.Status.APPROVED,
            self.Status.REJECTED,
            self.Status.CANCELLED,
        ]


class WorkflowRequestFile(models.Model):
    request = models.ForeignKey(
        WorkflowRequest,
        on_delete=models.CASCADE,
        related_name="files",
    )

    field_name = models.CharField(
        max_length=100,
    )

    file = models.FileField(
        upload_to="workflow_requests/%Y/%m/%d/",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Request #{self.request_id} - {self.file.name}"
    
class WorkflowAction(models.Model):

    class Action(models.TextChoices):
        SUBMIT = "SUBMIT", "Submit"
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"
        REQUEST_CHANGES = "REQUEST_CHANGES", "Request Changes"
        COMMENT = "COMMENT", "Comment"
        CANCEL = "CANCEL", "Cancel"

    request = models.ForeignKey(
        WorkflowRequest,
        on_delete=models.CASCADE,
        related_name="actions",
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="workflow_actions",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )

    comment = models.TextField(blank=True)

    from_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        related_name="actions_from",
        null=True,
        blank=True,
    )

    to_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        related_name="actions_to",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"Request #{self.request_id} - "
            f"{self.get_action_display()} - "
            f"{self.performed_by}"
        )


def move_request(workflow_request, transition, user, comment=""):
    current_step = workflow_request.current_step

    if workflow_request.is_finished:
        raise ValueError(
            "This workflow request has already been completed."
        )

    if current_step != transition.step:
        raise ValueError(
            "This transition does not belong to the current step."
        )

    action_map = {
        WorkflowTransition.Action.APPROVE:
            WorkflowAction.Action.APPROVE,

        WorkflowTransition.Action.REJECT:
            WorkflowAction.Action.REJECT,

        WorkflowTransition.Action.REQUEST_CHANGES:
            WorkflowAction.Action.REQUEST_CHANGES,
    }

    action = action_map[transition.action]

    # Reject → workflow ends.
    if transition.action == WorkflowTransition.Action.REJECT:
        status = WorkflowRequest.Status.REJECTED
        target_step = None
        return_step = None

    # Request Changes → send back to applicant,
    # but remember the review stage we came from.
    elif transition.action == WorkflowTransition.Action.REQUEST_CHANGES:
        status = WorkflowRequest.Status.CHANGES_REQUESTED
        target_step = None
        return_step = current_step

    # Approve with no target → workflow completed.
    elif transition.target_step is None:
        status = WorkflowRequest.Status.APPROVED
        target_step = None
        return_step = None

    # Approve → move to the next review stage.
    else:
        status = WorkflowRequest.Status.IN_PROGRESS
        target_step = transition.target_step
        return_step = None

    WorkflowAction.objects.create(
        request=workflow_request,
        performed_by=user,
        action=action,
        comment=comment,
        from_step=current_step,
        to_step=target_step,
    )

    workflow_request.current_step = target_step
    workflow_request.return_step = return_step
    workflow_request.status = status

    workflow_request.save(
        update_fields=[
            "current_step",
            "return_step",
            "status",
            "updated_at",
        ]
    )

    return workflow_request

