# accounts/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from accounts.models import GuardianChild, User

def _recompute_is_guardian(user_id: int):
    if not user_id:
        return
    try:
        u = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    has_children = GuardianChild.objects.filter(guardian=u).exists()
    if u.is_guardian != has_children:
        u.is_guardian = has_children
        u.save(update_fields=["is_guardian"])

@receiver(pre_save, sender=GuardianChild)
def _stash_old_guardian(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = GuardianChild.objects.get(pk=instance.pk)
            instance._old_guardian_id = old.guardian_id
        except GuardianChild.DoesNotExist:
            instance._old_guardian_id = None
    else:
        instance._old_guardian_id = None

@receiver(post_save, sender=GuardianChild)
def _sync_is_guardian_on_save(sender, instance, **kwargs):
    # new/current guardian
    _recompute_is_guardian(instance.guardian_id)
    # old guardian (if changed)
    old_id = getattr(instance, "_old_guardian_id", None)
    if old_id and old_id != instance.guardian_id:
        _recompute_is_guardian(old_id)

@receiver(post_delete, sender=GuardianChild)
def _sync_is_guardian_on_delete(sender, instance, **kwargs):
    _recompute_is_guardian(instance.guardian_id)
