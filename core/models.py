from django.conf import settings
from django.db import models


# Create your models here.
# Workflow
# WorkflowStep
# WorkflowExecution
# WorkflowStepExecution
# FormField

class Workflow(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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

class WorkflowStepExecution(models.Model):
    execution = models.ForeignKey(WorkflowExecution, related_name='step_executions', on_delete=models.CASCADE)
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        ('waiting', 'Waiting'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('skipped', 'Skipped'),
        ('error', 'Error'),
    ])
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict)  # collected form data or result

class FormField(models.Model):
    step = models.ForeignKey(WorkflowStep, related_name='fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=[
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('email', 'Email'),
        ('file', 'File'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('choice', 'Dropdown'),
    ])
    required = models.BooleanField(default=True)
    choices = models.TextField(blank=True)  # CSV: e.g. "Option1,Option2"
