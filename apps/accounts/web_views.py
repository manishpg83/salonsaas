from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .web_forms import LoginForm, RegisterForm

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Creating the user fires apps.salons' post_save signal, which
            # gives them a Salon + OWNER Membership automatically.
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                full_name=form.cleaned_data["full_name"],
                password=form.cleaned_data["password"],
            )
            auth_login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                auth_login(request, user)
                return redirect("dashboard")
            error = "Invalid email or password."
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form, "error": error})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect("login")
