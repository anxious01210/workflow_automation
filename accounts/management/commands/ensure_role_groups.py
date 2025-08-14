# # accounts/management/commands/ensure_role_groups.py
# from django.core.management.base import BaseCommand
# from django.contrib.auth.models import Group
# from accounts.models import ROLE_SLUGS
#
#
# class Command(BaseCommand):
#     def handle(self, *args, **opts):
#         for slug in ROLE_SLUGS:
#             Group.objects.get_or_create(name=slug)
#         self.stdout.write(self.style.SUCCESS("Role groups ensured"))



# accounts/management/commands/ensure_role_groups.py
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "DEPRECATED: use `python manage.py sync_roles`. This forwards to it."

    def handle(self, *args, **opts):
        call_command("sync_roles")  # portals/management/commands/sync_roles.py
        self.stdout.write(self.style.SUCCESS("Forwarded to sync_roles"))
