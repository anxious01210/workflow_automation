from django.utils import timezone
from .models import ExternalDirectory, SyncJob

def get_syncer(directory):
    if directory.provider == "azure":
        from .syncers.azure import AzureSyncer
        return AzureSyncer(directory)
    elif directory.provider == "google":
        from .syncers.google import GoogleSyncer
        return GoogleSyncer(directory)
    else:
        raise ValueError(f"Unknown provider: {directory.provider}")

def test_connection(directory):
    syncer = get_syncer(directory)
    ok = syncer.test_connection()
    directory.last_status = "success"
    directory.last_error = ""
    directory.save(update_fields=["last_status","last_error"])
    return ok

def enqueue_run_now(directory):
    directory.next_run_at = timezone.now()
    directory.save(update_fields=["next_run_at"])

# --- scheduling helpers ---
def compute_next_run(directory, now=None):
    now = timezone.localtime(now or timezone.now())
    if directory.schedule_kind == "interval":
        minutes = max(1, directory.interval_minutes or 60)
        return now + timezone.timedelta(minutes=minutes)
    else:
        try:
            from croniter import croniter
        except Exception:
            # Fallback: run again in 60 minutes if croniter missing
            return now + timezone.timedelta(minutes=60)
        itr = croniter(directory.cron_expr or "0 * * * *", now)
        return itr.get_next(datetime_type=type(now))
