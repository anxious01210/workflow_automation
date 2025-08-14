from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from portals.roles import ROLE_MAP


class Command(BaseCommand):
    help = "Sync role_* groups and assign portal permissions (idempotent)."

    def handle(self, *args, **options):
        ct = ContentType.objects.get(app_label="portals", model="portalaccess")
        for role_name, perm_list in ROLE_MAP.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            perms = Permission.objects.filter(
                content_type=ct,
                codename__in=[p.split(".")[-1] for p in perm_list],
            )
            group.permissions.set(perms)  # keep in sync with ROLE_MAP
            group.save()
            self.stdout.write(self.style.SUCCESS(f"Synced {role_name} ({perms.count()} perms)"))
        self.stdout.write(self.style.SUCCESS("Done."))
