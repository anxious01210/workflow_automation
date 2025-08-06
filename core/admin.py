from django.contrib import admin
from .models import Workflow, WorkflowStep, WorkflowExecution, WorkflowStepExecution, FormField
from django.utils.html import format_html
from django.urls import reverse
import json
from django.utils.safestring import mark_safe
from django.db import models
from django.forms import Textarea

# Register your models here.


admin.site.register(FormField)


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ("workflow", "name", "step_type", "order")
    readonly_fields = ("pretty_config",)
    fields = ("workflow", "name", "step_type", "config", "order", "pretty_config")

    formfield_overrides = {
        models.JSONField: {
            "widget": Textarea(attrs={"style": "width: 100%; min-width: 80%; font-family: monospace;"})
        }
    }

    def pretty_config(self, obj):
        try:
            formatted = json.dumps(obj.config, indent=2)
            return mark_safe(f'''
            <style>
                .admin-summary-link {{
                    color: var(--link-fg, #2a6496);
                    text-decoration: none;
                    cursor: pointer;
                    font-weight: bold;
                    transition: color 0.2s ease;
                }}
                .admin-summary-link:hover {{
                    color: var(--link-hover-color, #205081);
                    text-decoration: underline;
                }}
            </style>
                    <details style="border: 1px solid #ccc; padding: 8px; border-radius: 6px; background: var(--body-bg);">
                    <summary class="admin-summary-link"> Click to expand the Workflow</summary>
                    <pre style="white-space: pre-wrap; font-family: monospace;">{formatted}</pre>
                </details>
            ''')
        except Exception as e:
            return f"Error rendering config: {e}"

    pretty_config.short_description = "Config (Read Only)"

    def has_add_permission(self, request):
        return False  # optional: disallow manual creation of steps


# ✅ Inline for WorkflowStepExecutions under WorkflowExecution
class StepExecutionInline(admin.TabularInline):
    model = WorkflowStepExecution
    extra = 0
    fields = ("step", "status", "started_at", "completed_at", "short_data")
    readonly_fields = fields
    show_change_link = False

    def short_data(self, obj):
        return str(obj.data)[:80] + "..." if obj.data else "-"

    short_data.short_description = "Submitted Data"


# ✅ Inline for WorkflowExecutions under Workflow
class WorkflowExecutionInline(admin.TabularInline):
    model = WorkflowExecution
    extra = 0
    readonly_fields = ("initiator", "status", "started_at", "finished_at", "execution_link")
    fields = ("initiator", "status", "started_at", "finished_at", "execution_link")
    show_change_link = False

    def execution_link(self, obj):
        url = reverse("admin:core_workflowexecution_change", args=[obj.id])
        return format_html('<a href="{}" target="_blank">View</a>', url)

    execution_link.short_description = "Details"


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "is_active", "created_at", "builder_link", 'preview_link')
    inlines = [WorkflowExecutionInline]

    def builder_link(self, obj):
        url = reverse("core:workflow_builder", args=[obj.id])
        return format_html('<a href="{}" target="_blank">🔧 Open Builder</a>', url)

    builder_link.short_description = "Builder"

    def preview_link(self, obj):
        url = reverse('core:workflow_preview', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">Preview Form</a>', url)

    preview_link.short_description = "Preview"
    preview_link.allow_tags = True


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'workflow', 'initiator', 'status', 'started_at', 'finished_at')
    readonly_fields = ('workflow', 'initiator', 'status', 'started_at', 'finished_at')
    inlines = [StepExecutionInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WorkflowStepExecution)
class WorkflowStepExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'execution', 'step', 'status', 'started_at', 'completed_at')
    readonly_fields = ('execution', 'step', 'status', 'started_at', 'completed_at', 'formatted_data')
    fields = ('execution', 'step', 'status', 'started_at', 'completed_at', 'formatted_data')

    def formatted_data(self, obj):
        try:
            formatted = json.dumps(obj.data, indent=2)
            return mark_safe(f'''
                <style>
                    .admin-summary-link {{
                        color: var(--link-fg, #2a6496);
                        text-decoration: none;
                        cursor: pointer;
                        font-weight: bold;
                        transition: color 0.2s ease;
                    }}
                    .admin-summary-link:hover {{
                        color: var(--link-hover-color, #205081);
                        text-decoration: underline;
                    }}
                </style>
                        <details style="border: 1px solid #ccc; padding: 8px; border-radius: 6px; background: var(--body-bg);">
                        <summary class="admin-summary-link"> Click to view submitted data</summary>
                        <pre style="white-space: pre-wrap; font-family: monospace;">{formatted}</pre>
                    </details>
            ''')
        except Exception as e:
            return f"Invalid JSON: {e}"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
