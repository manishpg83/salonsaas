from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import salon_member_required
from apps.salons.models import Role

from .forms import (
    ProductCategoryForm,
    ProductForm,
    PurchaseForm,
    PurchaseItemForm,
    ServiceProductForm,
    StockAdjustmentForm,
    SupplierForm,
)
from .models import (
    Product,
    ProductCategory,
    Purchase,
    PurchaseItem,
    ServiceProduct,
    StockTransaction,
    Supplier,
)
from .stock import record_transaction


def _require_manager(request):
    """Inventory carries purchase cost and supplier data — bookkeeping, not
    front-desk work, same reasoning as apps/staff (salary) and billing's
    Expenses (CLAUDE.md §4.3's plain-if pattern)."""
    if request.membership.role not in (Role.OWNER, Role.MANAGER):
        raise PermissionDenied


def _recalculate_purchase(purchase):
    items = list(purchase.items.all())
    total = sum((item.line_total for item in items), Decimal("0.00"))
    purchase.total = total
    purchase.save(update_fields=["total"])


# --- Suppliers -------------------------------------------------------------


@salon_member_required
def supplier_list_view(request):
    _require_manager(request)
    suppliers = Supplier.objects.filter(salon=request.salon)
    return render(request, "inventory/supplier_list.html", {"suppliers": suppliers})


@salon_member_required
def supplier_create_view(request):
    _require_manager(request)
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.salon = request.salon
            supplier.save()
            messages.success(request, f"{supplier.name} added.")
            return redirect("supplier-list")
    else:
        form = SupplierForm()
    return render(request, "inventory/supplier_form.html", {"form": form, "supplier": None})


@salon_member_required
def supplier_edit_view(request, pk):
    _require_manager(request)
    supplier = get_object_or_404(Supplier, pk=pk, salon=request.salon)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"{supplier.name} updated.")
            return redirect("supplier-list")
    else:
        form = SupplierForm(instance=supplier)
    return render(request, "inventory/supplier_form.html", {"form": form, "supplier": supplier})


@require_POST
@salon_member_required
def supplier_delete_view(request, pk):
    _require_manager(request)
    supplier = get_object_or_404(Supplier, pk=pk, salon=request.salon)
    supplier.delete()
    messages.success(request, f"{supplier.name} removed.")
    return redirect("supplier-list")


# --- Product categories -----------------------------------------------------


@salon_member_required
def category_list_view(request):
    _require_manager(request)
    categories = ProductCategory.objects.filter(salon=request.salon)
    return render(request, "inventory/category_list.html", {"categories": categories})


@salon_member_required
def category_create_view(request):
    _require_manager(request)
    if request.method == "POST":
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.salon = request.salon
            category.save()
            messages.success(request, f"{category.name} added.")
            return redirect("product-category-list")
    else:
        form = ProductCategoryForm()
    return render(request, "inventory/category_form.html", {"form": form, "category": None})


@salon_member_required
def category_edit_view(request, pk):
    _require_manager(request)
    category = get_object_or_404(ProductCategory, pk=pk, salon=request.salon)
    if request.method == "POST":
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"{category.name} updated.")
            return redirect("product-category-list")
    else:
        form = ProductCategoryForm(instance=category)
    return render(
        request, "inventory/category_form.html", {"form": form, "category": category}
    )


@require_POST
@salon_member_required
def category_delete_view(request, pk):
    _require_manager(request)
    category = get_object_or_404(ProductCategory, pk=pk, salon=request.salon)
    category.delete()
    messages.success(request, f"{category.name} removed.")
    return redirect("product-category-list")


# --- Products ----------------------------------------------------------------


@salon_member_required
def product_list_view(request):
    _require_manager(request)
    products = Product.objects.filter(salon=request.salon).select_related("category", "supplier")
    return render(request, "inventory/product_list.html", {"products": products})


@salon_member_required
def product_create_view(request):
    _require_manager(request)
    if request.method == "POST":
        form = ProductForm(request.POST, salon=request.salon)
        if form.is_valid():
            product = form.save(commit=False)
            product.salon = request.salon
            product.save()
            messages.success(request, f"{product.name} added.")
            return redirect("product-list")
    else:
        form = ProductForm(salon=request.salon)
    return render(request, "inventory/product_form.html", {"form": form, "product": None})


@salon_member_required
def product_edit_view(request, pk):
    _require_manager(request)
    product = get_object_or_404(Product, pk=pk, salon=request.salon)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product, salon=request.salon)
        if form.is_valid():
            form.save()
            messages.success(request, f"{product.name} updated.")
            return redirect("product-list")
    else:
        form = ProductForm(instance=product, salon=request.salon)
    return render(request, "inventory/product_form.html", {"form": form, "product": product})


@require_POST
@salon_member_required
def product_delete_view(request, pk):
    _require_manager(request)
    product = get_object_or_404(Product, pk=pk, salon=request.salon)
    product.delete()
    messages.success(request, f"{product.name} removed.")
    return redirect("product-list")


@salon_member_required
def product_detail_view(request, pk):
    _require_manager(request)
    product = get_object_or_404(Product, pk=pk, salon=request.salon)
    return render(
        request,
        "inventory/product_detail.html",
        {
            "product": product,
            "transactions": product.stock_transactions.all(),
            "adjust_form": StockAdjustmentForm(),
            "recipes": product.consumption_recipes.select_related("service"),
            "recipe_form": ServiceProductForm(salon=request.salon),
        },
    )


@require_POST
@salon_member_required
def product_adjust_stock_view(request, pk):
    _require_manager(request)
    product = get_object_or_404(Product, pk=pk, salon=request.salon)
    form = StockAdjustmentForm(request.POST)
    if form.is_valid():
        record_transaction(
            salon=request.salon,
            product=product,
            transaction_type=StockTransaction.Type.ADJUST,
            quantity=form.cleaned_data["quantity"],
            reference=form.cleaned_data["reason"],
        )
        messages.success(request, "Stock adjusted.")
    else:
        messages.error(request, "Could not adjust stock — check the values.")
    return redirect("product-detail", pk=product.pk)


@require_POST
@salon_member_required
def product_recipe_add_view(request, pk):
    _require_manager(request)
    product = get_object_or_404(Product, pk=pk, salon=request.salon)
    form = ServiceProductForm(request.POST, salon=request.salon)
    if form.is_valid():
        ServiceProduct.objects.update_or_create(
            salon=request.salon,
            product=product,
            service=form.cleaned_data["service"],
            defaults={"quantity": form.cleaned_data["quantity"]},
        )
        messages.success(request, "Recipe saved.")
    else:
        messages.error(request, "Could not save recipe — check the values.")
    return redirect("product-detail", pk=product.pk)


@require_POST
@salon_member_required
def product_recipe_delete_view(request, pk, recipe_pk):
    _require_manager(request)
    product = get_object_or_404(Product, pk=pk, salon=request.salon)
    recipe = get_object_or_404(ServiceProduct, pk=recipe_pk, product=product, salon=request.salon)
    recipe.delete()
    messages.success(request, "Recipe removed.")
    return redirect("product-detail", pk=product.pk)


# --- Purchases -----------------------------------------------------------------


@salon_member_required
def purchase_list_view(request):
    _require_manager(request)
    purchases = Purchase.objects.filter(salon=request.salon).select_related("supplier")
    return render(request, "inventory/purchase_list.html", {"purchases": purchases})


@salon_member_required
def purchase_create_view(request):
    _require_manager(request)
    if request.method == "POST":
        form = PurchaseForm(request.POST, salon=request.salon)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.salon = request.salon
            purchase.save()
            messages.success(request, "Purchase created — add items below.")
            return redirect("purchase-detail", pk=purchase.pk)
    else:
        form = PurchaseForm(salon=request.salon)
    return render(request, "inventory/purchase_form.html", {"form": form})


@salon_member_required
def purchase_detail_view(request, pk):
    _require_manager(request)
    purchase = get_object_or_404(
        Purchase.objects.select_related("supplier"), pk=pk, salon=request.salon
    )
    return render(
        request,
        "inventory/purchase_detail.html",
        {
            "purchase": purchase,
            "items": purchase.items.select_related("product"),
            "item_form": PurchaseItemForm(salon=request.salon),
        },
    )


@require_POST
@salon_member_required
def purchase_add_item_view(request, pk):
    _require_manager(request)
    purchase = get_object_or_404(Purchase, pk=pk, salon=request.salon)
    form = PurchaseItemForm(request.POST, salon=request.salon)
    if form.is_valid():
        item = form.save(commit=False)
        item.salon = request.salon
        item.purchase = purchase
        item.save()
        record_transaction(
            salon=request.salon,
            product=item.product,
            transaction_type=StockTransaction.Type.IN,
            quantity=item.quantity,
            reference=f"Purchase #{purchase.pk}",
        )
        _recalculate_purchase(purchase)
        messages.success(request, "Item added — stock updated.")
    else:
        messages.error(request, "Could not add item — check the values.")
    return redirect("purchase-detail", pk=purchase.pk)
