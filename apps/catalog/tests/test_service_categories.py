import pytest

from apps.catalog.models import ServiceCategory
from apps.core.testing import assert_no_cross_tenant_access

pytestmark = pytest.mark.django_db


def test_create_list_retrieve_update_delete_category(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")

    create = client.post("/api/v1/catalog/categories/", {"name": "Hair"}, format="json")
    assert create.status_code == 201
    category_id = create.json()["id"]

    list_response = client.get("/api/v1/catalog/categories/")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    detail_url = f"/api/v1/catalog/categories/{category_id}/"

    retrieve = client.get(detail_url)
    assert retrieve.status_code == 200
    assert retrieve.json()["name"] == "Hair"

    update = client.patch(detail_url, {"name": "Hair & Spa"}, format="json")
    assert update.status_code == 200
    assert update.json()["name"] == "Hair & Spa"

    delete = client.delete(detail_url)
    assert delete.status_code == 204
    assert not ServiceCategory.objects.filter(id=category_id).exists()


def test_create_category_requires_name(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")

    response = client.post("/api/v1/catalog/categories/", {}, format="json")

    assert response.status_code == 400
    assert "name" in response.json()


def test_duplicate_category_name_within_same_salon_is_rejected(make_authenticated_client):
    client = make_authenticated_client("owner@example.com")
    client.post("/api/v1/catalog/categories/", {"name": "Hair"}, format="json")

    response = client.post("/api/v1/catalog/categories/", {"name": "Hair"}, format="json")

    assert response.status_code == 400


def test_categories_are_scoped_to_the_current_salon(make_authenticated_client):
    client_a = make_authenticated_client("owner-a@example.com")
    client_b = make_authenticated_client("owner-b@example.com")

    client_a.post("/api/v1/catalog/categories/", {"name": "Hair"}, format="json")
    client_b.post("/api/v1/catalog/categories/", {"name": "Spa"}, format="json")

    response = client_a.get("/api/v1/catalog/categories/")

    names = [category["name"] for category in response.json()["results"]]
    assert names == ["Hair"]


def test_category_created_by_one_salon_is_invisible_and_unwritable_by_another(make_authenticated_client):
    client_a = make_authenticated_client("owner-a@example.com")
    client_b = make_authenticated_client("owner-b@example.com")

    create = client_a.post("/api/v1/catalog/categories/", {"name": "Hair"}, format="json")
    detail_url = f"/api/v1/catalog/categories/{create.json()['id']}/"

    assert_no_cross_tenant_access(client_b, detail_url)
