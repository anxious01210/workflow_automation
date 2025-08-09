from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import GuardianChild


@receiver([post_save, post_delete], sender=GuardianChild)
def _sync_is_guardian(sender, instance, **kwargs):
    p = instance.guardian
    has_children = GuardianChild.objects.filter(guardian=p).exists()
    if p.is_guardian != has_children:
        p.is_guardian = has_children
        p.save(update_fields=["is_guardian"])
