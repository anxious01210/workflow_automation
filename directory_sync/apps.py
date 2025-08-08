from django.apps import AppConfig


class DirectorySyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'directory_sync'

    def ready(self):
        # Start the embedded scheduler once per process
        from .scheduler import start_scheduler_once
        start_scheduler_once()
