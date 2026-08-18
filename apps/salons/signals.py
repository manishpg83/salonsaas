from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Membership, Role, Salon


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_owner_salon_and_membership(sender, instance, created, **kwargs):
    """A self-serve signup is always "start your own salon" — so every new
    (non-superuser) user gets a fresh Salon and an OWNER Membership for it.
    Superusers are the SaaS-side Super Admin, not salon owners, so they're
    excluded. Full salon details are filled in by the Phase 1.4 onboarding
    wizard; this just gives tenancy something to resolve immediately."""

    if not created or instance.is_superuser:
        return

    salon = Salon.objects.create(name=f"{instance.full_name}'s Salon")
    Membership.objects.create(user=instance, salon=salon, role=Role.OWNER, is_current=True)
