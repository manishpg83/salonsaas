from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import SalonScopedModel

# Every stock quantity in this app (current_stock, min_stock, ledger
# entries, purchase/recipe quantities) uses this same shape — not every
# product is sold or consumed as a whole unit (e.g. 0.5 of a bottle per
# service), so these are decimal, not integer.
QUANTITY_KWARGS = {"max_digits": 10, "decimal_places": 2}


class Supplier(SalonScopedModel):
    name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductCategory(SalonScopedModel):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name


class Product(SalonScopedModel):
    """`current_stock` is derived, not user-entered — same "stored but
    recalculated" pattern as Invoice.total (Phase 6.1): it's the running sum
    of this product's StockTransaction ledger, recalculated by the view
    whenever a transaction is created. A new product always starts at 0;
    opening stock is added via a Purchase (IN) or a manual adjustment
    (ADJUST), never set directly, so the ledger stays the single source of
    truth."""

    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_stock = models.DecimalField(default=0, **QUANTITY_KWARGS)
    min_stock = models.DecimalField(default=0, **QUANTITY_KWARGS)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["salon", "sku"], name="unique_product_sku_per_salon"),
        ]

    @property
    def is_low_stock(self):
        return self.current_stock <= self.min_stock

    def __str__(self):
        return f"{self.name} ({self.sku})"


class StockTransaction(SalonScopedModel):
    """One ledger entry. `quantity` is the signed change in stock (positive
    adds, negative removes) — `type` is descriptive/for filtering only, it
    doesn't flip the sign, so Product.current_stock is always just the sum
    of every transaction's `quantity` for that product."""

    class Type(models.TextChoices):
        IN = "IN", "Stock in"
        OUT = "OUT", "Stock out"
        ADJUST = "ADJUST", "Manual adjustment"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_transactions")
    type = models.CharField(max_length=10, choices=Type.choices)
    quantity = models.DecimalField(**QUANTITY_KWARGS)
    reference = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.quantity >= 0 else ""
        return f"{self.get_type_display()} {sign}{self.quantity} — {self.product.name}"


class Purchase(SalonScopedModel):
    """`total` is derived from `items`, recalculated the same way as
    Invoice.total (Phase 6.1) — stored for cheap list-page reads, not
    user-entered."""

    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchases"
    )
    date = models.DateField()
    notes = models.TextField(blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Purchase #{self.pk}"


class ServiceProduct(SalonScopedModel):
    """Optional per-service consumption recipe (Phase 7.2): how much of a
    product gets used up whenever `service` is performed. Managed from the
    product side (apps/inventory) since apps/catalog is still the Phase 0-2
    DRF-only app with no template pages of its own to host this on."""

    service = models.ForeignKey("catalog.Service", on_delete=models.CASCADE, related_name="+")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="consumption_recipes")
    quantity = models.DecimalField(
        default=1, validators=[MinValueValidator(0)], **QUANTITY_KWARGS
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["service", "product"], name="unique_service_product_recipe"
            ),
        ]

    def __str__(self):
        return f"{self.service.name} uses {self.quantity} x {self.product.name}"


class PurchaseItem(SalonScopedModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="+")
    quantity = models.DecimalField(validators=[MinValueValidator(0)], **QUANTITY_KWARGS)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def line_total(self):
        return self.unit_cost * self.quantity

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
