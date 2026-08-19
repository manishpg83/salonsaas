from django.db import models

from apps.core.models import SalonScopedModel


class Staff(SalonScopedModel):
    """An employee profile (stylist, beautician, receptionist, ...).

    `membership` is optional and separate from `role`: not every staff member
    has a login (Membership + system Role), and `role` here is the person's
    job title (e.g. "Senior Stylist") shown on their profile — not the
    OWNER/MANAGER/RECEPTIONIST/STAFF permission level from salons.Role, which
    only applies to whoever also has a Membership.
    """

    membership = models.OneToOneField(
        "salons.Membership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profile",
    )
    branch = models.ForeignKey(
        "salons.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    name = models.CharField(max_length=150)
    # No file upload yet (django-storages isn't wired in until a later
    # phase, per requirements.txt) — same URL-only approach as Salon.logo_url.
    photo = models.URLField(blank=True)
    mobile = models.CharField(max_length=20)
    role = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField()
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Structured per-day schedule arrives with Phase 3.2's availability
    # model; this is a free-form placeholder in the meantime, same pattern
    # as Salon.business_hours.
    working_hours = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StaffService(SalonScopedModel):
    """One service a given staff member is able to perform."""

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="service_links")
    service = models.ForeignKey("catalog.Service", on_delete=models.CASCADE, related_name="+")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["staff", "service"], name="unique_service_per_staff"
            ),
        ]

    def __str__(self):
        return f"{self.staff.name} -> {self.service.name}"
