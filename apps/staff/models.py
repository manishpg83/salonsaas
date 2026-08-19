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


class WeekDay(models.IntegerChoices):
    """Matches Python's `date.weekday()` numbering (Monday=0..Sunday=6) so
    availability lookups can index straight off `date.weekday()` with no
    remapping."""

    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class StaffWorkingHours(SalonScopedModel):
    """One weekday's schedule for a staff member. A staff member has at most
    one row per weekday; a missing row means "not scheduled that day" (same
    as `is_off=True`) — the availability lookup (3.2) treats both the same
    way, so callers don't need to distinguish "never set up" from "marked
    off"."""

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="working_hours")
    weekday = models.PositiveSmallIntegerField(choices=WeekDay.choices)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_off = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday"]
        constraints = [
            models.UniqueConstraint(
                fields=["staff", "weekday"], name="unique_working_hours_per_staff_weekday"
            ),
        ]

    def __str__(self):
        return f"{self.staff.name} - {self.get_weekday_display()}"
