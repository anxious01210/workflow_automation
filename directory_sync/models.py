from django.db import models
from django.utils import timezone


class ExternalDirectory(models.Model):
    """
    A single external directory connection (e.g., one Azure tenant or one Google Workspace).
    The scheduler reads these rows to decide what/when to sync.
    """
    PROVIDERS = [
        ("azure", "Microsoft Entra ID (Azure AD)"),
        ("google", "Google Workspace"),
    ]
    SCHEDULE_KINDS = [
        ("interval", "Interval (minutes)"),
        ("cron", "Cron expression"),
    ]

    # Basic
    name = models.CharField(
        max_length=100,
        help_text="A short label shown in admin, e.g. “Main Entra ID (Prod)”."
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDERS,
        help_text="Which external directory to sync with."
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="If off, the scheduler ignores this connection (no runs)."
    )

    # Scheduling
    schedule_kind = models.CharField(
        max_length=10,
        choices=SCHEDULE_KINDS,
        default="interval",
        help_text="Use a simple minute interval or a cron expression for when this sync should run."
    )
    interval_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Run every N minutes (used when Schedule kind = Interval). Minimum = 1."
    )
    cron_expr = models.CharField(
        max_length=100,
        blank=True,
        help_text=(
            "Standard 5-field cron in your site’s local timezone (e.g., Asia/Baghdad). "
            "Example: 0 */2 * * *  → every 2 hours. Ignored when Schedule kind = Interval. "
            "Requires the ‘croniter’ package to honor cron exactly; otherwise falls back to hourly."
        )
    )

    # Provider config & feature toggles
    credentials = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Connection JSON for the provider. For Azure: "
            '{"tenant_id": "...", "client_id": "...", "client_secret": "..." }. '
            "Stored in the DB; rotate/regenerate secrets if they ever leak."
        )
    )
    allowed_domains = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Optional allow-list of email domains to keep (e.g., [\"school.edu\"]). "
        )
    )
    include_groups = models.BooleanField(
        default=True,
        help_text="Fetch and store group IDs on each user (groups_cache). Increases API calls/time."
    )
    include_licenses = models.BooleanField(
        default=True,
        help_text="Fetch license SKU codes per user (licenses). Increases API calls/time."
    )
    deprovision_missing = models.BooleanField(
        default=False,
        help_text=(
            "When ON, users that disappear from the directory are deactivated locally "
            "(is_active=False). With delta sync, @removed entries also deactivate."
        )
    )
    only_active = models.BooleanField(
        default=False,
        help_text=(
            "When ON, skip creating disabled accounts from the directory. "
            "If an existing user becomes disabled, mark them inactive. "
            "Active users continue to sync normally."
        )
    )

    # Status/progress (read-only in practice)
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last sync finished (shown in your local timezone in admin)."
    )
    next_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the scheduler plans to run next. ‘Run sync now’ sets this to now."
    )
    last_status = models.CharField(
        max_length=20,
        blank=True,
        help_text="Result of the last run (success / failed)."
    )
    last_error = models.TextField(
        blank=True,
        help_text="Most recent error text, if any. Cleared on a successful run."
    )
    delta_link = models.CharField(
        max_length=500,
        blank=True,
        help_text=(
            "Microsoft Graph delta cursor. Managed automatically; clearing forces a fresh delta crawl."
        )
    )

    class Meta:
        verbose_name = "External directory"
        verbose_name_plural = "External directories"

    def __str__(self):
        return f"{self.name} [{self.get_provider_display()}]"


class SyncJob(models.Model):
    """
    One execution of a sync. Created by the scheduler each time it runs.
    """
    directory = models.ForeignKey(
        ExternalDirectory,
        on_delete=models.CASCADE,
        help_text="Which external directory this job was run against."
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this job started."
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this job finished (set automatically on success/failure)."
    )
    status = models.CharField(
        max_length=20,
        default="running",
        help_text="Current state: running / success / failed."
    )
    created_count = models.IntegerField(
        default=0,
        help_text="How many user records were created in this run."
    )
    updated_count = models.IntegerField(
        default=0,
        help_text="How many user records were updated in this run."
    )
    deactivated_count = models.IntegerField(
        default=0,
        help_text="How many users were set inactive (disabled or missing)."
    )
    notes = models.TextField(
        blank=True,
        help_text="Free-form notes and sampled errors from the sync (for quick triage)."
    )

    def mark(self, *, status=None, created=None, updated=None, deactivated=None, notes=None):
        if status:
            self.status = status
        if created is not None:
            self.created_count = created
        if updated is not None:
            self.updated_count = updated
        if deactivated is not None:
            self.deactivated_count = deactivated
        if notes:
            self.notes = (self.notes or "") + ("\n" if self.notes else "") + notes
        if status in {"success", "failed"} and not self.finished_at:
            self.finished_at = timezone.now()
        self.save()

    class Meta:
        verbose_name = "Sync job"
        verbose_name_plural = "Sync jobs"

    def __str__(self):
        # helpful in the admin list
        ts = self.started_at.strftime("%Y-%m-%d %H:%M") if self.started_at else "—"
        return f"{self.directory.name} — {self.status} @ {ts}"
