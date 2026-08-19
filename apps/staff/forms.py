from django import forms

from apps.catalog.models import Service
from apps.salons.models import Membership

from .models import Staff


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = [
            "name",
            "photo",
            "mobile",
            "role",
            "branch",
            "membership",
            "joining_date",
            "salary",
            "commission_percent",
            "working_hours",
            "is_active",
        ]
        widgets = {
            "joining_date": forms.DateInput(attrs={"type": "date"}),
            "working_hours": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch"].queryset = self.fields["branch"].queryset.filter(salon=salon)
        # A Membership can back at most one Staff profile (OneToOneField) —
        # exclude ones already linked, except the one this instance already
        # holds, so editing a staff member doesn't drop it from the choices.
        membership_qs = Membership.objects.filter(salon=salon, staff_profile__isnull=True)
        if self.instance.pk and self.instance.membership_id:
            membership_qs = Membership.objects.filter(salon=salon, staff_profile__isnull=True) | Membership.objects.filter(
                pk=self.instance.membership_id
            )
        self.fields["membership"].queryset = membership_qs


class StaffServicesForm(forms.Form):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["services"].queryset = Service.objects.filter(salon=salon).select_related(
            "category"
        )
