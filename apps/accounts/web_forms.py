from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(forms.Form):
    email = forms.EmailField()
    full_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)

        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
