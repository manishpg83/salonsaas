import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import OTP

User = get_user_model()

pytestmark = pytest.mark.django_db


def _create_user(email="owner@example.com", password="a-strong-password-123"):
    return User.objects.create_user(email=email, full_name="Owner Person", password=password)


def test_request_otp_creates_a_login_otp_and_prints_it_to_console(capsys):
    user = _create_user()

    response = APIClient().post("/api/v1/auth/otp/request/", {"email": user.email}, format="json")

    assert response.status_code == 200
    otp = OTP.objects.get(user=user, purpose=OTP.Purpose.LOGIN)
    assert capsys.readouterr().out.strip().endswith(otp.code)


def test_request_otp_for_unknown_email_returns_same_generic_response():
    response = APIClient().post(
        "/api/v1/auth/otp/request/", {"email": "nobody@example.com"}, format="json"
    )

    assert response.status_code == 200
    assert not OTP.objects.exists()


def test_verify_otp_with_correct_code_returns_tokens_and_consumes_it():
    user = _create_user()
    APIClient().post("/api/v1/auth/otp/request/", {"email": user.email}, format="json")
    otp = OTP.objects.get(user=user, purpose=OTP.Purpose.LOGIN)

    response = APIClient().post(
        "/api/v1/auth/otp/verify/", {"email": user.email, "code": otp.code}, format="json"
    )

    assert response.status_code == 200
    body = response.json()
    assert "access" in body
    assert "refresh" in body

    otp.refresh_from_db()
    assert otp.used_at is not None


def test_verify_otp_rejects_wrong_code():
    user = _create_user()
    APIClient().post("/api/v1/auth/otp/request/", {"email": user.email}, format="json")

    response = APIClient().post(
        "/api/v1/auth/otp/verify/", {"email": user.email, "code": "000000"}, format="json"
    )

    assert response.status_code == 400


def test_verify_otp_rejects_reused_code():
    user = _create_user()
    APIClient().post("/api/v1/auth/otp/request/", {"email": user.email}, format="json")
    otp = OTP.objects.get(user=user, purpose=OTP.Purpose.LOGIN)

    client = APIClient()
    first = client.post(
        "/api/v1/auth/otp/verify/", {"email": user.email, "code": otp.code}, format="json"
    )
    second = client.post(
        "/api/v1/auth/otp/verify/", {"email": user.email, "code": otp.code}, format="json"
    )

    assert first.status_code == 200
    assert second.status_code == 400
