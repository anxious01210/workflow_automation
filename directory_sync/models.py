from django.db import models
from django.utils import timezone

class ExternalDirectory(models.Model):
    PROVIDERS = [
        ("azure", "Microsoft Entra ID (Azure AD)"),
        ("google", "Google Workspace"),
    ]
    SCHEDULE_KINDS = [("interval", "Interval (minutes)"), ("cron", "Cron expression")]

    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    is_enabled = models.BooleanField(default=True)

    # Scheduling
    schedule_kind = models.CharField(max_length=10, choices=SCHEDULE_KINDS, default="interval")
    interval_minutes = models.PositiveIntegerField(default=60)
    cron_expr = models.CharField(max_length=100, blank=True)  # e.g. "0 */2 * * *"

    # Provider config
    credentials = models.JSONField(default=dict, blank=True)    # tenant_id, client_id, secret, etc.
    allowed_domains = models.JSONField(default=list, blank=True)
    include_groups = models.BooleanField(default=True)
    include_licenses = models.BooleanField(default=True)
    deprovision_missing = models.BooleanField(default=False)

    # Status
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=20, blank=True)  # success/failed
    last_error = models.TextField(blank=True)
    delta_link = models.CharField(max_length=500, blank=True)

    def __str__(self): return f"{self.name} [{self.get_provider_display()}]"

class SyncJob(models.Model):
    directory = models.ForeignKey(ExternalDirectory, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="running")  # running/success/failed
    created_count = models.IntegerField(default=0)
    updated_count = models.IntegerField(default=0)
    deactivated_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    def mark(self, *, status=None, created=None, updated=None, deactivated=None, notes=None):
        if status: self.status = status
        if created is not None: self.created_count = created
        if updated is not None: self.updated_count = updated
        if deactivated is not None: self.deactivated_count = deactivated
        if notes: self.notes = (self.notes or "") + ("\n" if self.notes else "") + notes
        if status in {"success", "failed"} and not self.finished_at:
            self.finished_at = timezone.now()
        self.save()
