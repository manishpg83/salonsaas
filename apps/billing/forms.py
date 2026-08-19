from django import forms

from .models import Expense, Invoice, InvoiceItem, Payment


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["description", "quantity", "unit_price", "tax_percent"]


class InvoiceDiscountForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["discount"]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["method", "amount", "reference"]


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "date", "note"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }
