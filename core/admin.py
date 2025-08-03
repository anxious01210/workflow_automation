from django.contrib import admin
from .models import Workflow, WorkflowStep, WorkflowExecution, WorkflowStepExecution, FormField
from django.utils.html import format_html
from django.urls import reverse

# Register your models here.

admin.site.register(WorkflowStep)
admin.site.register(WorkflowExecution)
admin.site.register(WorkflowStepExecution)
admin.site.register(FormField)



# admin.site.register(Workflow)
@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "is_active", "created_at", "builder_link")

    def builder_link(self, obj):
        url = reverse("core:workflow_builder", args=[obj.id])
        return format_html('<a href="{}" target="_blank">🔧 Open Builder</a>', url)

    builder_link.short_description = "Builder"