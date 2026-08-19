import pytest

from apps.crm.models import Customer

pytestmark = pytest.mark.django_db


def _payload(**overrides):
    payload = {
        "name": "Kavya Reddy",
        "mobile": "9876500000",
        "email": "kavya@example.com",
        "gender": "FEMALE",
        "dob": "1995-04-12",
        "anniversary": "",
        "address": "221 Brigade Road",
        "source": "WALK_IN",
        "notes": "Prefers organic products.",
    }
    payload.update(overrides)
    return payload


def test_customer_list_requires_login(client):
    response = client.get("/customers/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_create_list_view_edit_and_delete_customer(make_web_client):
    client, membership = make_web_client("owner@example.com")

    create = client.post("/customers/new/", _payload())
    assert create.status_code == 302
    customer = Customer.objects.get(salon=membership.salon)
    assert customer.name == "Kavya Reddy"

    list_response = client.get("/customers/")
    assert "Kavya Reddy" in list_response.content.decode()

    detail = client.get(f"/customers/{customer.pk}/")
    assert detail.status_code == 200
    assert "Kavya Reddy" in detail.content.decode()

    edit = client.post(f"/customers/{customer.pk}/edit/", _payload(name="Kavya Rao"))
    assert edit.status_code == 302
    customer.refresh_from_db()
    assert customer.name == "Kavya Rao"

    delete = client.post(f"/customers/{customer.pk}/delete/")
    assert delete.status_code == 302
    assert not Customer.objects.filter(pk=customer.pk).exists()


def test_create_customer_requires_name_and_mobile(make_web_client):
    client, _membership = make_web_client("owner@example.com")

    response = client.post("/customers/new/", _payload(name="", mobile=""))

    assert response.status_code == 200
    assert "This field is required" in response.content.decode()
    assert not Customer.objects.exists()


def test_duplicate_mobile_within_the_same_salon_is_rejected(make_web_client):
    client, _membership = make_web_client("owner@example.com")
    client.post("/customers/new/", _payload(name="First Customer"))

    response = client.post("/customers/new/", _payload(name="Second Customer"))

    assert response.status_code == 200
    assert "already exists" in response.content.decode()
    assert Customer.objects.count() == 1


def test_same_mobile_is_allowed_across_different_salons(make_web_client):
    client_a, _membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")

    assert client_a.post("/customers/new/", _payload()).status_code == 302
    assert client_b.post("/customers/new/", _payload()).status_code == 302
    assert Customer.objects.count() == 2


def test_customers_are_scoped_to_the_current_salon(make_web_client):
    client_a, _membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    client_a.post("/customers/new/", _payload(name="Customer A", mobile="9111111111"))
    client_b.post("/customers/new/", _payload(name="Customer B", mobile="9222222222"))

    response = client_a.get("/customers/")

    body = response.content.decode()
    assert "Customer A" in body
    assert "Customer B" not in body


def test_customer_created_by_one_salon_is_unreachable_from_another(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    client_a.post("/customers/new/", _payload())
    customer = Customer.objects.get(salon=membership_a.salon)

    assert client_b.get(f"/customers/{customer.pk}/").status_code == 404
    assert client_b.get(f"/customers/{customer.pk}/edit/").status_code == 404
    assert client_b.post(f"/customers/{customer.pk}/edit/", _payload()).status_code == 404
    assert client_b.post(f"/customers/{customer.pk}/delete/").status_code == 404
    assert Customer.objects.filter(pk=customer.pk).exists()


def test_search_by_name_and_mobile(make_web_client):
    client, _membership = make_web_client("owner@example.com")
    client.post("/customers/new/", _payload(name="Kavya Reddy", mobile="9876500000"))
    client.post("/customers/new/", _payload(name="Meera Iyer", mobile="9876511111"))
    client.get("/customers/")  # drain the "added" flash messages before asserting on page content

    by_name = client.get("/customers/", {"q": "Kavya"})
    assert "Kavya Reddy" in by_name.content.decode()
    assert "Meera Iyer" not in by_name.content.decode()

    by_mobile = client.get("/customers/", {"q": "9876511111"})
    assert "Meera Iyer" in by_mobile.content.decode()
    assert "Kavya Reddy" not in by_mobile.content.decode()
