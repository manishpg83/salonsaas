"""Shared stock-mutation helpers — the single place that creates a
StockTransaction and keeps Product.current_stock in sync with it. Used by
apps.inventory's own views (purchases, manual adjustments) and by
apps.scheduling (Phase 7.2 service consumption) so every stock change goes
through the same ledger-then-recalculate path."""

from decimal import Decimal

from django.db.models import Sum

from .models import ServiceProduct, StockTransaction


def recalculate_stock(product):
    total = product.stock_transactions.aggregate(total=Sum("quantity"))["total"]
    product.current_stock = total if total is not None else Decimal("0.00")
    product.save(update_fields=["current_stock"])


def record_transaction(salon, product, transaction_type, quantity, reference=""):
    StockTransaction.objects.create(
        salon=salon,
        product=product,
        type=transaction_type,
        quantity=quantity,
        reference=reference,
    )
    recalculate_stock(product)


def consume_for_appointment(appointment):
    """Phase 7.2: decrement stock for each service's optional consumption
    recipe when an appointment completes. Idempotent by construction, not by
    a flag — this is only ever called right after
    Appointment.transition_to(COMPLETED) succeeds in
    apps.scheduling.views.appointment_status_view, and that transition can
    only succeed once per appointment (IN_SERVICE -> COMPLETED is the only
    way in, COMPLETED -> PAID the only way out — a second attempt to
    transition to COMPLETED raises ValueError before this ever runs again,
    see Appointment.VALID_TRANSITIONS)."""
    for line in appointment.services.select_related("service"):
        recipes = ServiceProduct.objects.filter(
            salon=appointment.salon, service=line.service
        ).select_related("product")
        for recipe in recipes:
            record_transaction(
                salon=appointment.salon,
                product=recipe.product,
                transaction_type=StockTransaction.Type.OUT,
                quantity=-recipe.quantity,
                reference=f"Appointment #{appointment.pk} — {line.service.name}",
            )
