from django.contrib import admin, messages
from django.utils import timezone
from .models import ExternalDirectory, SyncJob
from .utils import enqueue_run_now, test_connection
from django.db import models as dj_models

@admin.register(ExternalDirectory)
class ExternalDirectoryAdmin(admin.ModelAdmin):
    list_display = ("name","provider","is_enabled","schedule_kind","interval_minutes","cron_expr","last_run_at","next_run_at","last_status")
    list_filter = ("provider","is_enabled","schedule_kind","last_status")
    readonly_fields = ("last_run_at","next_run_at","last_status","last_error")
    formfield_overrides = {
        dj_models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows":2})},
    }

    actions = ["action_run_now","action_test_connection","action_pause","action_resume"]

    @admin.action(description="Run sync now (enqueue)")
    def action_run_now(self, request, queryset):
        for d in queryset:
            enqueue_run_now(d)
        self.message_user(request, f"Enqueued {queryset.count()} directory sync(s). Scheduler will pick them up within ~30s.", level=messages.SUCCESS)

    @admin.action(description="Test connection")
    def action_test_connection(self, request, queryset):
        ok, errs = 0, 0
        for d in queryset:
            try:
                test_connection(d)
                ok += 1
            except Exception as e:
                errs += 1
                d.last_status, d.last_error = "failed", str(e)
                d.save(update_fields=["last_status","last_error"])
        msg = f"Tested {ok+errs} — OK: {ok}, Failed: {errs}"
        level = messages.SUCCESS if errs == 0 else messages.WARNING
        self.message_user(request, msg, level=level)

    @admin.action(description="Pause (disable)")
    def action_pause(self, request, queryset):
        updated = queryset.update(is_enabled=False)
        self.message_user(request, f"Paused {updated} directories.", level=messages.INFO)

    @admin.action(description="Resume (enable)")
    def action_resume(self, request, queryset):
        updated = queryset.update(is_enabled=True)
        self.message_user(request, f"Resumed {updated} directories.", level=messages.SUCCESS)

@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ("directory","status","started_at","finished_at","created_count","updated_count","deactivated_count")
    list_filter = ("status","directory__provider")
    readonly_fields = ("directory","status","started_at","finished_at","created_count","updated_count","deactivated_count","notes")
