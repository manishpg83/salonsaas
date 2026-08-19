import pytest

from apps.billing.models import Expense
from apps.salons.models import Role

pytestmark = pytest.mark.django_db


def _payload(**overrides):
    payload = {
        "category": "SUPPLIES",
        "amount": "1250.00",
        "date": "2026-08-15",
        "note": "Shampoo and conditioner restock",
    }
    payload.update(overrides)
    return payload


def test_expense_list_requires_login(client):
    response = client.get("/expenses/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_owner_can_create_list_edit_and_delete_expense(make_web_client):
    client, membership = make_web_client("owner@example.com")

    create = client.post("/expenses/new/", _payload())
    assert create.status_code == 302
    expense = Expense.objects.get(salon=membership.salon)
    assert expense.category == "SUPPLIES"
    assert expense.amount == 1250

    list_response = client.get("/expenses/")
    assert "Shampoo and conditioner restock" in list_response.content.decode()

    edit = client.post(f"/expenses/{expense.pk}/edit/", _payload(amount="1500.00"))
    assert edit.status_code == 302
    expense.refresh_from_db()
    assert expense.amount == 1500

    delete = client.post(f"/expenses/{expense.pk}/delete/")
    assert delete.status_code == 302
    assert not Expense.objects.filter(pk=expense.pk).exists()


def test_create_expense_requires_category_amount_and_date(make_web_client):
    client, _membership = make_web_client("owner@example.com")

    response = client.post("/expenses/new/", _payload(category="", amount="", date=""))

    assert response.status_code == 200
    assert "This field is required" in response.content.decode()
    assert not Expense.objects.exists()


def test_receptionist_role_is_denied_expense_management(make_web_client):
    client, membership = make_web_client("receptionist@example.com")
    membership.role = Role.RECEPTIONIST
    membership.save(update_fields=["role"])

    response = client.get("/expenses/")

    assert response.status_code == 403


def test_expenses_are_scoped_to_the_current_salon(make_web_client):
    client_a, _membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    client_a.post("/expenses/new/", _payload(note="Salon A rent"))
    client_b.post("/expenses/new/", _payload(note="Salon B rent"))

    response = client_a.get("/expenses/")

    body = response.content.decode()
    assert "Salon A rent" in body
    assert "Salon B rent" not in body


def test_expense_created_by_one_salon_is_unreachable_from_another(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    client_a.post("/expenses/new/", _payload())
    expense = Expense.objects.get(salon=membership_a.salon)

    assert client_b.get(f"/expenses/{expense.pk}/edit/").status_code == 404
    assert client_b.post(f"/expenses/{expense.pk}/edit/", _payload()).status_code == 404
    assert client_b.post(f"/expenses/{expense.pk}/delete/").status_code == 404
    assert Expense.objects.filter(pk=expense.pk).exists()
