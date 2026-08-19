from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name",
            "mobile",
            "email",
            "gender",
            "dob",
            "anniversary",
            "address",
            "source",
            "notes",
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "anniversary": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, salon, **kwargs):
        self.salon = salon
        super().__init__(*args, **kwargs)

    def clean_mobile(self):
        mobile = self.cleaned_data["mobile"]
        duplicate = Customer.objects.filter(salon=self.salon, mobile=mobile)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("A customer with this mobile number already exists.")
        return mobile
