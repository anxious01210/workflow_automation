import os, threading, time, traceback
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import ExternalDirectory, SyncJob
from .utils import get_syncer, compute_next_run

_started_flag = False

def start_scheduler_once():
    """Start exactly once (avoid duplicate threads with the autoreloader)."""
    global _started_flag
    if _started_flag:
        return
    # Guard for the dev autoreloader
    if settings.DEBUG and os.environ.get("RUN_MAIN") != "true":
        return
    _started_flag = True

    tick = getattr(settings, "DIRECTORY_SYNC_TICK_SECONDS", 30)
    t = threading.Thread(target=_loop, args=(tick,), daemon=True, name="directory-sync-scheduler")
    t.start()

def _loop(tick_seconds: int):
    while True:
        now = timezone.now()
        due = ExternalDirectory.objects.filter(is_enabled=True).filter(
            Q(next_run_at__isnull=True) | Q(next_run_at__lte=now)
        )
        for d in due:
            # Skip if a job for this directory is already running
            if SyncJob.objects.filter(directory=d, status="running").exists():
                continue

            job = SyncJob.objects.create(directory=d, status="running")
            try:
                syncer = get_syncer(d)
                result = syncer.sync()  # dict(created=.., updated=.., deactivated=.., notes="..")
                job.mark(
                    status="success",
                    created=result.get("created", 0),
                    updated=result.get("updated", 0),
                    deactivated=result.get("deactivated", 0),
                    notes=result.get("notes", ""),
                )
                d.last_status, d.last_error = "success", ""
            except Exception as e:
                job.mark(status="failed", notes=f"{e}\n{traceback.format_exc()}")
                d.last_status, d.last_error = "failed", str(e)

            d.last_run_at = timezone.now()
            d.next_run_at = compute_next_run(d, now=timezone.now())
            d.save(update_fields=["last_run_at", "last_status", "last_error", "next_run_at"])

        time.sleep(tick_seconds)
