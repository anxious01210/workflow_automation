import time, traceback
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from directory_sync.models import ExternalDirectory, SyncJob
from directory_sync.utils import get_syncer, compute_next_run

TICK_SECONDS = 30

class Command(BaseCommand):
    help = "Runs the directory sync scheduler (DB-driven)."

    def handle(self, *args, **opts):
        self.stdout.write(self.style.SUCCESS("Directory scheduler started."))
        while True:
            now = timezone.now()
            due = ExternalDirectory.objects.filter(is_enabled=True).filter(
                # run if next_run_at is null (first run) or due
                models.Q(next_run_at__isnull=True) | models.Q(next_run_at__lte=now)
            )
            for d in due:
                # Avoid overlapping runs: if a 'running' job exists, skip
                if SyncJob.objects.filter(directory=d, status="running").exists():
                    continue

                # Create job row first
                job = SyncJob.objects.create(directory=d, status="running")

                try:
                    syncer = get_syncer(d)
                    result = syncer.sync()
                    job.mark(
                        status="success",
                        created=result.get("created",0),
                        updated=result.get("updated",0),
                        deactivated=result.get("deactivated",0),
                        notes=result.get("notes",""),
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
                d.save(update_fields=["last_run_at","last_status","last_error","next_run_at"])

            time.sleep(TICK_SECONDS)
