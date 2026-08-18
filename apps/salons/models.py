from django.conf import settings
from django.db import models

from apps.core.models import SalonScopedModel, TimeStampedModel


class Role(models.TextChoices):
    """Membership role — see CLAUDE.md §4.3. Super Admin is Django
    `is_superuser` on User, not a role here."""

    OWNER = "OWNER", "Owner"
    MANAGER = "MANAGER", "Manager"
    RECEPTIONIST = "RECEPTIONIST", "Receptionist"
    STAFF = "STAFF", "Staff"


class Salon(TimeStampedModel):
    """The tenant root. Not salon-scoped — everything else scopes to this."""

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Branch(SalonScopedModel):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.name} ({self.salon.name})"


class Membership(SalonScopedModel):
    """Links a User to a Salon with a Role. A user can hold one Membership
    per salon; `is_current` marks which salon is active for them right now
    (CLAUDE.md: "the active salon is chosen at login/context") — enforced to
    at most one per user by the partial unique constraint below."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    is_current = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "salon"], name="unique_membership_per_user_and_salon"
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_current=True),
                name="unique_current_membership_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.salon.name} ({self.role})"
