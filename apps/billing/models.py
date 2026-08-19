from decimal import Decimal

from django.db import models
from django.db.models import Sum

from apps.core.models import SalonScopedModel


class Invoice(SalonScopedModel):
    """Generated from a completed Appointment (CLAUDE.md §7 Phase 6.1) — one
    invoice per appointment. `subtotal`/`tax_total`/`total` are derived from
    `items` (same "stored but recalculated" pattern as Appointment.price in
    Phase 5.1), not user-entered."""

    appointment = models.OneToOneField(
        "scheduling.Appointment", on_delete=models.CASCADE, related_name="invoice"
    )
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    @property
    def invoice_number(self):
        return f"INV-{self.pk:06d}"

    @property
    def paid_total(self):
        return self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    @property
    def balance_due(self):
        return self.total - self.paid_total

    @property
    def is_fully_paid(self):
        return self.total > 0 and self.paid_total >= self.total

    def __str__(self):
        return self.invoice_number


class InvoiceItem(SalonScopedModel):
    """One billed line. `service` is set when the line came straight from
    the appointment's booked services (auto-generated at invoice creation);
    it's left blank for an ad-hoc product/adjustment line added manually at
    checkout — there's no Product catalog yet (that's Phase 7), so ad-hoc
    lines are just free-text `description` + price."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey(
        "catalog.Service", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def line_subtotal(self):
        return self.unit_price * self.quantity

    @property
    def line_tax(self):
        return (self.line_subtotal * self.tax_percent / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def line_total(self):
        return self.line_subtotal + self.line_tax

    def __str__(self):
        return f"{self.description} x{self.quantity}"


class Payment(SalonScopedModel):
    """One payment towards an Invoice. A 'split' payment (CLAUDE.md's
    payment-methods list) isn't its own method — it's simply more than one
    Payment row against the same invoice, each with its own method."""

    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        UPI = "UPI", "UPI"
        CARD = "CARD", "Card"
        BANK = "BANK", "Bank transfer"
        ONLINE = "ONLINE", "Online"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_method_display()} ₹{self.amount} for {self.invoice}"


class Expense(SalonScopedModel):
    """A business expense — simple CRUD (CLAUDE.md §7 Phase 6.2). Feeds
    profit = revenue - expenses in Phase 10's reports; nothing reads this
    yet."""

    class Category(models.TextChoices):
        RENT = "RENT", "Rent"
        UTILITIES = "UTILITIES", "Utilities"
        SUPPLIES = "SUPPLIES", "Supplies"
        SALARIES = "SALARIES", "Salaries"
        MARKETING = "MARKETING", "Marketing"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        OTHER = "OTHER", "Other"

    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_category_display()} - ₹{self.amount} ({self.date})"
