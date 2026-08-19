from django import forms

from apps.catalog.models import Service

from .models import Product, ProductCategory, Purchase, PurchaseItem, ServiceProduct, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_phone", "contact_email", "address", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ["name"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "category",
            "supplier",
            "purchase_price",
            "selling_price",
            "min_stock",
            "expiry_date",
            "is_active",
        ]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ProductCategory.objects.filter(salon=salon)
        self.fields["supplier"].queryset = Supplier.objects.filter(salon=salon)
        self.fields["category"].required = False
        self.fields["supplier"].required = False


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["supplier", "date", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(salon=salon)
        self.fields["supplier"].required = False


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ["product", "quantity", "unit_cost"]

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(salon=salon)


class ServiceProductForm(forms.ModelForm):
    class Meta:
        model = ServiceProduct
        fields = ["service", "quantity"]

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(salon=salon, is_active=True)


class StockAdjustmentForm(forms.Form):
    """Not a ModelForm — `type` and `product` are set server-side (see
    apps/staff/forms.py's AvailabilityLookupForm for the same plain-Form
    pattern), only the delta and a human reason come from the user."""

    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Positive to add stock, negative to remove. Fractions are fine (e.g. 0.5).",
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 10, -3, or 0.5"}),
    )
    reason = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. stock count correction, damage"}),
    )
