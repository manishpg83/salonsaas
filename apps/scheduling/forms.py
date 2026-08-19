from django import forms
from django.forms import inlineformset_factory

from apps.catalog.models import Service
from apps.crm.models import Customer
from apps.staff.models import Staff

from .models import Appointment, AppointmentService


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["customer", "branch", "date", "time", "discount", "advance", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(salon=salon)
        self.fields["branch"].queryset = self.fields["branch"].queryset.filter(salon=salon)


class AppointmentServiceForm(forms.ModelForm):
    """No Meta here on purpose — inlineformset_factory below supplies
    model/fields, this class only adds the salon-scoping __init__ (same
    pattern as StaffForm/CustomerForm)."""

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(salon=salon, is_active=True)
        self.fields["staff"].queryset = Staff.objects.filter(salon=salon, is_active=True)


AppointmentServiceFormSet = inlineformset_factory(
    Appointment,
    AppointmentService,
    form=AppointmentServiceForm,
    fields=["service", "staff"],
    extra=2,
    can_delete=True,
)
