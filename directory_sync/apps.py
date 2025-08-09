from django.apps import AppConfig
from django.db.backends.signals import connection_created

_started = False

class DirectorySyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "directory_sync"

    def ready(self):
        from .scheduler import start_scheduler_once

        def _start_scheduler(*args, **kwargs):
            global _started
            if _started:
                return
            _started = True
            start_scheduler_once()
            # run once only
            connection_created.disconnect(_start_scheduler)

        # Start scheduler after DB connection is ready
        connection_created.connect(_start_scheduler)
