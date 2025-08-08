# accounts/management/commands/ensure_role_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import ROLE_SLUGS


class Command(BaseCommand):
    def handle(self, *args, **opts):
        for slug in ROLE_SLUGS:
            Group.objects.get_or_create(name=slug)
        self.stdout.write(self.style.SUCCESS("Role groups ensured"))
