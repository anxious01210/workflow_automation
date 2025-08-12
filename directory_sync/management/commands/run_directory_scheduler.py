import time, traceback
from django.core.management.base import BaseCommand
from django.utils import timezone
# from django.db import transaction
from datetime import timedelta
from directory_sync.models import ExternalDirectory, SyncJob
from directory_sync.utils import get_syncer, compute_next_run
from django.db.models import Q

TICK_SECONDS = 30
STALE_JOB_MINUTES = 30  # if a job 'runs' longer than this, consider it stale


class Command(BaseCommand):
    help = "Runs the directory sync scheduler (DB-driven)."

    def handle(self, *args, **opts):
        self.stdout.write(self.style.SUCCESS("Directory scheduler started."))

        # Boot-time cleanup: mark old 'running' jobs as failed so scheduler can proceed
        cutoff = timezone.now() - timedelta(minutes=STALE_JOB_MINUTES)
        stale = SyncJob.objects.filter(status="running", started_at__lt=cutoff)
        for j in stale:
            j.status = "failed"
            j.finished_at = timezone.now()
            j.notes = (j.notes or "") + f"\nAuto-failed as stale after restart (>{STALE_JOB_MINUTES}m)."
            j.save(update_fields=["status", "finished_at", "notes"])

        while True:
            now = timezone.now()
            due = ExternalDirectory.objects.filter(is_enabled=True).filter(
                # run if next_run_at is null (first run) or due
                Q(next_run_at__isnull=True) | Q(next_run_at__lte=now)
            )
            for d in due:
                # Avoid overlapping runs; auto-fail stale ones
                running = SyncJob.objects.filter(directory=d, status="running").first()
                if running:
                    cutoff = timezone.now() - timedelta(minutes=STALE_JOB_MINUTES)
                    if running.started_at and running.started_at < cutoff:
                        running.status = "failed"
                        running.finished_at = timezone.now()
                        running.notes = (running.notes or "") + f"\nAuto-failed as stale (>{STALE_JOB_MINUTES}m)."
                        running.save(update_fields=["status", "finished_at", "notes"])
                    else:
                        continue

                # Create job row first
                job = SyncJob.objects.create(directory=d, status="running")

                try:
                    syncer = get_syncer(d)
                    result = syncer.sync()
                    job.mark(
                        status="success",
                        created=result.get("created", 0),
                        updated=result.get("updated", 0),
                        deactivated=result.get("deactivated", 0),
                        notes=result.get("notes", ""),
                    )
                    d.last_run_at = timezone.now()
                    d.last_status = "success"
                    d.last_error = ""
                except Exception as e:
                    tb = traceback.format_exc()
                    job.mark(status="failed", notes=str(e) + "\n" + tb)
                    d.last_run_at = timezone.now()
                    d.last_status = "failed"
                    d.last_error = str(e)

                d.next_run_at = compute_next_run(d, now=timezone.now())
                d.save(update_fields=["last_run_at", "last_status", "last_error", "next_run_at"])

            time.sleep(TICK_SECONDS)
