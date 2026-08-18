from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SalonScopedModel(TimeStampedModel):
    """
    Base class for every salon-scoped business model (CLAUDE.md §4.2).

    `related_name='+'` disables the reverse accessor on Salon — with dozens
    of scoped models inheriting this, `salon.customer_set`,
    `salon.appointment_set`, etc. would clutter it for no benefit. Query the
    scoped model directly instead (always through `SalonScopedViewSet`).
    """

    salon = models.ForeignKey("salons.Salon", on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True
