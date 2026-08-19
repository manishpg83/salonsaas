from django.db import models

from apps.core.models import SalonScopedModel


class Appointment(SalonScopedModel):
    class Status(models.TextChoices):
        BOOKED = "BOOKED", "Booked"
        CONFIRMED = "CONFIRMED", "Confirmed"
        ARRIVED = "ARRIVED", "Arrived"
        IN_SERVICE = "IN_SERVICE", "In service"
        COMPLETED = "COMPLETED", "Completed"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No-show"

    # Which status a booking can move to from its current one. BOOKED can
    # skip straight to ARRIVED for a walk-in who never went through an
    # explicit confirmation step; everything else follows the natural
    # front-desk flow. PAID/CANCELLED/NO_SHOW are terminal.
    VALID_TRANSITIONS = {
        Status.BOOKED: [Status.CONFIRMED, Status.ARRIVED, Status.CANCELLED, Status.NO_SHOW],
        Status.CONFIRMED: [Status.ARRIVED, Status.CANCELLED, Status.NO_SHOW],
        Status.ARRIVED: [Status.IN_SERVICE, Status.CANCELLED],
        Status.IN_SERVICE: [Status.COMPLETED, Status.CANCELLED],
        Status.COMPLETED: [Status.PAID],
        Status.PAID: [],
        Status.CANCELLED: [],
        Status.NO_SHOW: [],
    }

    customer = models.ForeignKey(
        "crm.Customer", on_delete=models.CASCADE, related_name="appointments"
    )
    branch = models.ForeignKey(
        "salons.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    date = models.DateField()
    time = models.TimeField()
    # Derived from the AppointmentService lines (recalculated whenever they
    # change via appointment_services_view) — not user-entered.
    duration_minutes = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.customer.name} - {self.date} {self.time}"

    def next_statuses(self):
        return self.VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status):
        if new_status not in self.next_statuses():
            raise ValueError(
                f"Cannot move an appointment from {self.get_status_display()} to '{new_status}'."
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])


class AppointmentService(SalonScopedModel):
    """One service line within an appointment. `price`/`duration_minutes`
    are snapshotted from the Service when the line is added — a booking
    shouldn't silently change if the salon edits its price list later."""

    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="services"
    )
    service = models.ForeignKey("catalog.Service", on_delete=models.CASCADE, related_name="+")
    staff = models.ForeignKey(
        "staff.Staff", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.service.name} for {self.appointment}"
