import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import OTP

User = get_user_model()

pytestmark = pytest.mark.django_db


def _create_user(email="owner@example.com", password="a-strong-password-123"):
    return User.objects.create_user(email=email, full_name="Owner Person", password=password)


def test_forgot_password_creates_a_reset_otp_and_prints_it_to_console(capsys):
    user = _create_user()

    response = APIClient().post("/api/v1/auth/password/forgot/", {"email": user.email}, format="json")

    assert response.status_code == 200
    otp = OTP.objects.get(user=user, purpose=OTP.Purpose.PASSWORD_RESET)
    assert capsys.readouterr().out.strip().endswith(otp.code)


def test_forgot_password_for_unknown_email_returns_same_generic_response():
    response = APIClient().post(
        "/api/v1/auth/password/forgot/", {"email": "nobody@example.com"}, format="json"
    )

    assert response.status_code == 200
    assert not OTP.objects.exists()


def test_reset_password_with_correct_code_changes_the_password():
    user = _create_user()
    APIClient().post("/api/v1/auth/password/forgot/", {"email": user.email}, format="json")
    otp = OTP.objects.get(user=user, purpose=OTP.Purpose.PASSWORD_RESET)

    response = APIClient().post(
        "/api/v1/auth/password/reset/",
        {"email": user.email, "code": otp.code, "new_password": "a-new-strong-password-456"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("a-new-strong-password-456")

    login = APIClient().post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": "a-new-strong-password-456"},
        format="json",
    )
    assert login.status_code == 200


def test_reset_password_rejects_wrong_code():
    user = _create_user()
    APIClient().post("/api/v1/auth/password/forgot/", {"email": user.email}, format="json")

    response = APIClient().post(
        "/api/v1/auth/password/reset/",
        {"email": user.email, "code": "000000", "new_password": "a-new-strong-password-456"},
        format="json",
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.check_password("a-strong-password-123")


def test_reset_password_rejects_weak_new_password():
    user = _create_user()
    APIClient().post("/api/v1/auth/password/forgot/", {"email": user.email}, format="json")
    otp = OTP.objects.get(user=user, purpose=OTP.Purpose.PASSWORD_RESET)

    response = APIClient().post(
        "/api/v1/auth/password/reset/",
        {"email": user.email, "code": otp.code, "new_password": "123"},
        format="json",
    )

    assert response.status_code == 400
