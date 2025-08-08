from django.conf import settings
from django.db import models
from django.contrib.auth.models import Group


# Create your models here.
class Workflow(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def can_start(self, user):
        if self.is_public:
            return True
        if not user.is_authenticated:
            return False
        if self.allowed_groups.exists():
            if not user.groups.filter(id__in=self.allowed_groups.values_list("id", flat=True)).exists():
                return False
        if self.allowed_domains and getattr(user, "email_domain", None) not in self.allowed_domains:
            return False
        return True


class WorkflowStep(models.Model):
    STEP_TYPES = [
        ('form', 'Form Input'),
        ('email', 'Send Email'),
        ('timer', 'Delay Timer'),
        ('approval', 'Approval Step'),
        ('condition', 'Conditional Branch'),
        ('webhook', 'Webhook Call'),
    ]

    workflow = models.ForeignKey(Workflow, related_name='steps', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    step_type = models.CharField(max_length=50, choices=STEP_TYPES)
    config = models.JSONField(default=dict)  # dynamic: form fields, email content, etc.
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.workflow.name} – {self.name}"


class WorkflowExecution(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    initiator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    current_step = models.ForeignKey('WorkflowStepExecution', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Execution #{self.id} – {self.workflow.name}"


class WorkflowStepExecution(models.Model):
    execution = models.ForeignKey(WorkflowExecution, related_name='step_executions', on_delete=models.CASCADE)
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        ('waiting', 'Waiting'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('skipped', 'Skipped'),
        ('error', 'Error'),
    ], default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict)  # collected form data or result

    def __str__(self):
        return f"{self.execution} – {self.step.name} [{self.status}]"

# class FormField(models.Model):
#     step = models.ForeignKey(WorkflowStep, related_name='fields', on_delete=models.CASCADE)
#     label = models.CharField(max_length=255)
#
#     FIELD_TYPES = [
#         ('text', 'Text'),
#         ('textarea', 'Textarea'),
#         ('email', 'Email'),
#         ('phone', 'Phone'),
#         ('url', 'URL'),
#         ('file', 'File'),
#         ('number', 'Number'),
#         ('password', 'Password'),
#
#         ('date', 'Date'),
#         ('time', 'Time'),
#         ('datetime', 'DateTime'),
#
#         ('range_date', 'Date Range'),
#         ('range_time', 'Time Range'),
#         ('range_datetime', 'DateTime Range'),
#
#         ('choice', 'Dropdown'),
#         ('multi_choice', 'Multi-Select'),
#         ('checkbox', 'Checkbox'),
#
#         ('section_heading', 'Section Heading'),
#         ('html_note', 'HTML Note'),
#     ]
#     field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
#     required = models.BooleanField(default=True)
#     choices = models.TextField(blank=True, help_text="CSV format, e.g., Option1,Option2")
