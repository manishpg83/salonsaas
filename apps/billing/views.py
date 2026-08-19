from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import salon_member_required
from apps.salons.models import Role
from apps.scheduling.models import Appointment

from .forms import ExpenseForm, InvoiceDiscountForm, InvoiceItemForm, PaymentForm
from .models import Expense, Invoice, InvoiceItem, Payment


def _require_manager(request):
    """Expenses are bookkeeping, not front-desk work — restrict to
    OWNER/MANAGER, same reasoning (and pattern) as apps/staff."""
    if request.membership.role not in (Role.OWNER, Role.MANAGER):
        raise PermissionDenied


def _recalculate_invoice(invoice):
    items = list(invoice.items.all())
    subtotal = sum((item.line_subtotal for item in items), Decimal("0.00"))
    tax_total = sum((item.line_tax for item in items), Decimal("0.00"))
    invoice.subtotal = subtotal
    invoice.tax_total = tax_total
    invoice.total = subtotal + tax_total - invoice.discount
    invoice.save(update_fields=["subtotal", "tax_total", "total"])


@salon_member_required
def invoice_list_view(request):
    invoices = Invoice.objects.filter(salon=request.salon).select_related(
        "appointment", "appointment__customer"
    )
    return render(request, "billing/list.html", {"invoices": invoices})


@require_POST
@salon_member_required
def invoice_generate_view(request, appointment_pk):
    appointment = get_object_or_404(Appointment, pk=appointment_pk, salon=request.salon)

    if hasattr(appointment, "invoice"):
        return redirect("invoice-detail", pk=appointment.invoice.pk)

    if appointment.status != Appointment.Status.COMPLETED:
        messages.error(request, "Only a completed appointment can be invoiced.")
        return redirect("appointment-detail", pk=appointment.pk)

    invoice = Invoice.objects.create(
        salon=request.salon, appointment=appointment, discount=appointment.discount
    )
    for line in appointment.services.select_related("service"):
        InvoiceItem.objects.create(
            salon=request.salon,
            invoice=invoice,
            service=line.service,
            description=line.service.name,
            quantity=1,
            unit_price=line.price,
            tax_percent=line.service.tax_percent,
        )
    if appointment.advance > 0:
        Payment.objects.create(
            salon=request.salon,
            invoice=invoice,
            method=Payment.Method.ADVANCE,
            amount=appointment.advance,
            reference="Advance paid at booking",
        )
    _recalculate_invoice(invoice)
    if invoice.is_fully_paid:
        try:
            appointment.transition_to(Appointment.Status.PAID)
        except ValueError:
            pass  # already PAID (or otherwise not COMPLETED) — nothing to do
    messages.success(request, f"{invoice.invoice_number} generated.")
    return redirect("invoice-detail", pk=invoice.pk)


@salon_member_required
def invoice_detail_view(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("appointment", "appointment__customer"),
        pk=pk,
        salon=request.salon,
    )
    return render(
        request,
        "billing/detail.html",
        {
            "invoice": invoice,
            "items": invoice.items.all(),
            "payments": invoice.payments.all(),
            "item_form": InvoiceItemForm(),
            "discount_form": InvoiceDiscountForm(instance=invoice),
            "payment_form": PaymentForm(),
        },
    )


@require_POST
@salon_member_required
def invoice_add_item_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, salon=request.salon)
    form = InvoiceItemForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.salon = request.salon
        item.invoice = invoice
        item.save()
        _recalculate_invoice(invoice)
        messages.success(request, "Item added.")
    else:
        messages.error(request, "Could not add item — check the values.")
    return redirect("invoice-detail", pk=invoice.pk)


@require_POST
@salon_member_required
def invoice_update_discount_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, salon=request.salon)
    form = InvoiceDiscountForm(request.POST, instance=invoice)
    if form.is_valid():
        form.save()
        _recalculate_invoice(invoice)
        messages.success(request, "Discount updated.")
    else:
        messages.error(request, "Invalid discount.")
    return redirect("invoice-detail", pk=invoice.pk)


@require_POST
@salon_member_required
def invoice_add_payment_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, salon=request.salon)
    form = PaymentForm(request.POST)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.salon = request.salon
        payment.invoice = invoice
        payment.save()
        messages.success(request, "Payment recorded.")
        if invoice.is_fully_paid:
            try:
                invoice.appointment.transition_to(Appointment.Status.PAID)
                messages.success(request, "Appointment marked Paid.")
            except ValueError:
                pass  # already PAID (or otherwise not COMPLETED) — nothing to do
    else:
        messages.error(request, "Could not record payment — check the values.")
    return redirect("invoice-detail", pk=invoice.pk)


@salon_member_required
def expense_list_view(request):
    _require_manager(request)
    expenses = Expense.objects.filter(salon=request.salon)
    return render(request, "billing/expense_list.html", {"expenses": expenses})


@salon_member_required
def expense_create_view(request):
    _require_manager(request)
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.salon = request.salon
            expense.save()
            messages.success(request, "Expense added.")
            return redirect("expense-list")
    else:
        form = ExpenseForm()

    return render(request, "billing/expense_form.html", {"form": form, "expense": None})


@salon_member_required
def expense_edit_view(request, pk):
    _require_manager(request)
    expense = get_object_or_404(Expense, pk=pk, salon=request.salon)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated.")
            return redirect("expense-list")
    else:
        form = ExpenseForm(instance=expense)

    return render(request, "billing/expense_form.html", {"form": form, "expense": expense})


@require_POST
@salon_member_required
def expense_delete_view(request, pk):
    _require_manager(request)
    expense = get_object_or_404(Expense, pk=pk, salon=request.salon)
    expense.delete()
    messages.success(request, "Expense deleted.")
    return redirect("expense-list")
