from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import salon_member_required

from .forms import CustomerForm
from .models import Customer


@salon_member_required
def customer_list_view(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.filter(salon=request.salon)
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(mobile__icontains=query))
    return render(request, "crm/list.html", {"customers": customers, "query": query})


@salon_member_required
def customer_create_view(request):
    if request.method == "POST":
        form = CustomerForm(request.POST, salon=request.salon)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.salon = request.salon
            customer.save()
            messages.success(request, f"{customer.name} added.")
            return redirect("customer-list")
    else:
        form = CustomerForm(salon=request.salon)

    return render(request, "crm/form.html", {"form": form, "customer": None})


@salon_member_required
def customer_edit_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk, salon=request.salon)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer, salon=request.salon)
        if form.is_valid():
            form.save()
            messages.success(request, f"{customer.name} updated.")
            return redirect("customer-list")
    else:
        form = CustomerForm(instance=customer, salon=request.salon)

    return render(request, "crm/form.html", {"form": form, "customer": customer})


@require_POST
@salon_member_required
def customer_delete_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk, salon=request.salon)
    customer.delete()
    messages.success(request, f"{customer.name} removed.")
    return redirect("customer-list")


@salon_member_required
def customer_detail_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk, salon=request.salon)
    # Appointments/payments/reviews sections are placeholders until Phase
    # 5/6/V2 exist — the template renders their empty states directly, no
    # querysets to pass yet.
    return render(request, "crm/detail.html", {"customer": customer})
