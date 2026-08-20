from django import forms

from apps.crm.models import Customer

from .models import MessageTemplate


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ["body", "is_active"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}


class SendTestMessageForm(forms.Form):
    """Cross-tenant FK restriction on `customer` — same `salon` kwarg
    pattern as AppointmentForm/CustomerForm (CLAUDE.md §4.4)."""

    customer = forms.ModelChoiceField(queryset=Customer.objects.none(), label="Send test to")

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(salon=salon)
