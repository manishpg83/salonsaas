import pytest

from apps.catalog.models import Service
from apps.core.testing import assert_no_cross_tenant_access

pytestmark = pytest.mark.django_db


def _create_category(client, name="Hair"):
    response = client.post("/api/v1/catalog/categories/", {"name": name}, format="json")
    return response.json()["id"]


def _service_payload(category_id, **overrides):
    payload = {
        "category": category_id,
        "name": "Haircut",
        "price": "500.00",
        "duration_minutes": 30,
    }
    payload.update(overrides)
    return payload


def test_create_list_retrieve_update_delete_service(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")
    category_id = _create_category(client)

    create = client.post("/api/v1/catalog/services/", _service_payload(category_id), format="json")
    assert create.status_code == 201, create.json()
    service_id = create.json()["id"]

    list_response = client.get("/api/v1/catalog/services/")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    detail_url = f"/api/v1/catalog/services/{service_id}/"

    retrieve = client.get(detail_url)
    assert retrieve.status_code == 200
    assert retrieve.json()["name"] == "Haircut"

    update = client.patch(detail_url, {"price": "600.00"}, format="json")
    assert update.status_code == 200
    assert update.json()["price"] == "600.00"

    delete = client.delete(detail_url)
    assert delete.status_code == 204
    assert not Service.objects.filter(id=service_id).exists()


def test_create_service_requires_category_price_and_duration(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")

    response = client.post("/api/v1/catalog/services/", {"name": "Haircut"}, format="json")

    assert response.status_code == 400
    body = response.json()
    assert "category" in body
    assert "price" in body
    assert "duration_minutes" in body


def test_service_rejects_a_category_belonging_to_another_salon(make_authenticated_client):
    client_a = make_authenticated_client("owner-a@example.com")
    client_b = make_authenticated_client("owner-b@example.com")
    other_salons_category_id = _create_category(client_b)

    response = client_a.post(
        "/api/v1/catalog/services/", _service_payload(other_salons_category_id), format="json"
    )

    assert response.status_code == 400
    assert "category" in response.json()


def test_services_are_scoped_to_the_current_salon(make_authenticated_client):
    client_a = make_authenticated_client("owner-a@example.com")
    client_b = make_authenticated_client("owner-b@example.com")
    category_a = _create_category(client_a)
    category_b = _create_category(client_b)

    client_a.post("/api/v1/catalog/services/", _service_payload(category_a), format="json")
    client_b.post(
        "/api/v1/catalog/services/", _service_payload(category_b, name="Facial"), format="json"
    )

    response = client_a.get("/api/v1/catalog/services/")

    names = [service["name"] for service in response.json()["results"]]
    assert names == ["Haircut"]


def test_service_created_by_one_salon_is_invisible_and_unwritable_by_another(make_authenticated_client):
    client_a = make_authenticated_client("owner-a@example.com")
    client_b = make_authenticated_client("owner-b@example.com")
    category_id = _create_category(client_a)

    create = client_a.post("/api/v1/catalog/services/", _service_payload(category_id), format="json")
    detail_url = f"/api/v1/catalog/services/{create.json()['id']}/"

    assert_no_cross_tenant_access(client_b, detail_url)
