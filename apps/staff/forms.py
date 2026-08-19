from django import forms
from django.forms import modelformset_factory

from apps.catalog.models import Service
from apps.salons.models import Membership

from .models import Staff, StaffWorkingHours


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
            "is_active",
        ]
        widgets = {
            "joining_date": forms.DateInput(attrs={"type": "date"}),
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


# Exactly one row per weekday (see StaffWorkingHours.Meta.unique_together) —
# the view ensures all 7 rows exist before building this, so extra=0 and no
# add/delete UI is needed. `weekday` isn't a form field: it's fixed per row
# and only ever set by the view via get_or_create, never client-editable.
StaffWorkingHoursFormSet = modelformset_factory(
    StaffWorkingHours,
    fields=["start_time", "end_time", "is_off"],
    widgets={
        "start_time": forms.TimeInput(attrs={"type": "time"}),
        "end_time": forms.TimeInput(attrs={"type": "time"}),
    },
    extra=0,
    can_delete=False,
)


class AvailabilityLookupForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.none())
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, salon, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(
            salon=salon, is_active=True
        ).select_related("category")
