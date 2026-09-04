from django.contrib import admin

from .models import (
    Application,
    ApplicationEligibilityRule,
    ApplicationField,
    Workflow,
    WorkflowAction,
    WorkflowRequest,
    WorkflowRequestFile,
    WorkflowStep,
    WorkflowTransition,
)


class ApplicationFieldInline(admin.TabularInline):
    model = ApplicationField
    extra = 1
    ordering = ("order",)


class ApplicationEligibilityRuleInline(admin.TabularInline):
    model = ApplicationEligibilityRule
    extra = 1


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "is_active",
        "created_by",
        "created_at",
    )

    list_filter = (
        "category",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [
        ApplicationFieldInline,
        ApplicationEligibilityRuleInline,
    ]


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 1
    ordering = ("order",)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "application",
        "is_active",
        "created_by",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "application__name",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [
        WorkflowStepInline,
    ]


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "workflow",
        "assigned_role",
        "order",
    )

    list_filter = (
        "assigned_role",
        "workflow",
    )

    search_fields = (
        "name",
        "workflow__name",
    )

    ordering = (
        "workflow",
        "order",
    )


@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "step",
        "action",
        "target_step",
    )

    list_filter = (
        "action",
        "step__workflow",
    )

    search_fields = (
        "name",
        "step__name",
        "target_step__name",
    )


@admin.register(WorkflowRequest)
class WorkflowRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "workflow",
        "submitted_by",
        "current_step",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "workflow",
        "created_at",
    )

    search_fields = (
        "submitted_by__username",
        "workflow__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(WorkflowRequestFile)
class WorkflowRequestFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request",
        "field_name",
        "file",
        "uploaded_at",
    )

    list_filter = (
        "uploaded_at",
    )

    search_fields = (
        "field_name",
        "request__workflow__name",
        "request__submitted_by__username",
    )

    readonly_fields = (
        "uploaded_at",
    )


@admin.register(WorkflowAction)
class WorkflowActionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request",
        "performed_by",
        "action",
        "from_step",
        "to_step",
        "created_at",
    )

    list_filter = (
        "action",
        "created_at",
    )

    search_fields = (
        "request__workflow__name",
        "performed_by__username",
        "comment",
    )

    readonly_fields = (
        "request",
        "performed_by",
        "action",
        "comment",
        "from_step",
        "to_step",
        "created_at",
    )