import pytest

from apps.catalog.models import Package, PackageService

pytestmark = pytest.mark.django_db


def _create_service(client, name="Haircut", price="500.00", duration_minutes=30):
    category_id = client.post(
        "/api/v1/catalog/categories/", {"name": f"{name} category"}, format="json"
    ).json()["id"]
    response = client.post(
        "/api/v1/catalog/services/",
        {
            "category": category_id,
            "name": name,
            "price": price,
            "duration_minutes": duration_minutes,
        },
        format="json",
    )
    return response.json()["id"]


def _package_payload(*service_items, **overrides):
    payload = {
        "name": "Bridal Combo",
        "price": "2500.00",
        "items": [{"service": sid, "quantity": qty} for sid, qty in service_items],
    }
    payload.update(overrides)
    return payload


def test_create_package_bundling_services(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")
    haircut_id = _create_service(client, name="Haircut")
    facial_id = _create_service(client, name="Facial")

    response = client.post(
        "/api/v1/catalog/packages/",
        _package_payload((haircut_id, 2), (facial_id, 1)),
        format="json",
    )

    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["name"] == "Bridal Combo"
    assert len(body["items"]) == 2

    package = Package.objects.get(id=body["id"])
    assert PackageService.objects.filter(package=package).count() == 2
    assert PackageService.objects.get(package=package, service_id=haircut_id).quantity == 2


def test_list_and_retrieve_package(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")
    haircut_id = _create_service(client)
    create = client.post(
        "/api/v1/catalog/packages/", _package_payload((haircut_id, 1)), format="json"
    )
    package_id = create.json()["id"]

    list_response = client.get("/api/v1/catalog/packages/")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    retrieve = client.get(f"/api/v1/catalog/packages/{package_id}/")
    assert retrieve.status_code == 200
    assert retrieve.json()["items"][0]["service"] == haircut_id


def test_package_requires_at_least_one_item(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")

    response = client.post(
        "/api/v1/catalog/packages/", {"name": "Empty", "price": "100.00", "items": []}, format="json"
    )

    assert response.status_code == 400
    assert "items" in response.json()


def test_package_rejects_duplicate_service_in_items(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")
    haircut_id = _create_service(client)

    response = client.post(
        "/api/v1/catalog/packages/",
        _package_payload((haircut_id, 1), (haircut_id, 1)),
        format="json",
    )

    assert response.status_code == 400
    assert "items" in response.json()


def test_package_rejects_a_service_from_another_salon(make_authenticated_client):
    client_a = make_authenticated_client("owner-a@example.com")
    client_b = make_authenticated_client("owner-b@example.com")
    other_salons_service_id = _create_service(client_b)

    response = client_a.post(
        "/api/v1/catalog/packages/",
        _package_payload((other_salons_service_id, 1)),
        format="json",
    )

    assert response.status_code == 400
    assert "items" in response.json()


def test_package_has_no_update_or_delete_endpoint(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")
    haircut_id = _create_service(client)
    create = client.post(
        "/api/v1/catalog/packages/", _package_payload((haircut_id, 1)), format="json"
    )
    detail_url = f"/api/v1/catalog/packages/{create.json()['id']}/"

    assert client.patch(detail_url, {"name": "New name"}, format="json").status_code == 405
    assert client.delete(detail_url).status_code == 405


def test_package_created_by_one_salon_is_invisible_to_another(make_authenticated_client):
    client_a = make_authenticated_client("owner-a@example.com")
    client_b = make_authenticated_client("owner-b@example.com")
    haircut_id = _create_service(client_a)

    create = client_a.post(
        "/api/v1/catalog/packages/", _package_payload((haircut_id, 1)), format="json"
    )
    detail_url = f"/api/v1/catalog/packages/{create.json()['id']}/"

    assert client_b.get(detail_url).status_code == 404
    assert client_b.get("/api/v1/catalog/packages/").json()["count"] == 0
