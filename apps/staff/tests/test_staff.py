import pytest

from apps.catalog.models import Service, ServiceCategory
from apps.salons.models import Role
from apps.staff.models import Staff, StaffService

pytestmark = pytest.mark.django_db


def _staff_payload(**overrides):
    payload = {
        "name": "Priya Sharma",
        "photo": "",
        "mobile": "9876543210",
        "role": "Senior Stylist",
        "branch": "",
        "membership": "",
        "joining_date": "2026-01-15",
        "salary": "25000",
        "commission_percent": "10",
        "working_hours": "{}",
        "is_active": "on",
    }
    payload.update(overrides)
    return payload


def _make_service(salon, name="Haircut"):
    category = ServiceCategory.objects.create(salon=salon, name="Hair")
    return Service.objects.create(
        salon=salon, category=category, name=name, price="500.00", duration_minutes=30
    )


def test_staff_list_requires_login(client):
    response = client.get("/staff/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_owner_can_create_list_edit_and_delete_staff(make_web_client):
    client, membership = make_web_client("owner@example.com")

    create = client.post("/staff/new/", _staff_payload())
    assert create.status_code == 302
    staff = Staff.objects.get(salon=membership.salon)
    assert staff.name == "Priya Sharma"
    assert staff.role == "Senior Stylist"

    list_response = client.get("/staff/")
    assert list_response.status_code == 200
    assert "Priya Sharma" in list_response.content.decode()

    edit = client.post(f"/staff/{staff.pk}/edit/", _staff_payload(name="Priya Verma"))
    assert edit.status_code == 302
    staff.refresh_from_db()
    assert staff.name == "Priya Verma"

    delete = client.post(f"/staff/{staff.pk}/delete/")
    assert delete.status_code == 302
    assert not Staff.objects.filter(pk=staff.pk).exists()


def test_create_edit_and_services_pages_render(make_web_client):
    client, membership = make_web_client("owner@example.com")
    client.post("/staff/new/", _staff_payload())
    staff = Staff.objects.get(salon=membership.salon)

    assert client.get("/staff/new/").status_code == 200
    assert client.get(f"/staff/{staff.pk}/edit/").status_code == 200
    assert client.get(f"/staff/{staff.pk}/services/").status_code == 200


def test_create_staff_requires_name_mobile_and_joining_date(make_web_client):
    client, _membership = make_web_client("owner@example.com")

    response = client.post("/staff/new/", _staff_payload(name="", mobile="", joining_date=""))

    assert response.status_code == 200
    body = response.content.decode()
    assert "This field is required" in body
    assert not Staff.objects.exists()


def test_receptionist_role_is_denied_staff_management(make_web_client):
    client, membership = make_web_client("receptionist@example.com")
    membership.role = Role.RECEPTIONIST
    membership.save(update_fields=["role"])

    response = client.get("/staff/")

    assert response.status_code == 403


def test_staff_are_scoped_to_the_current_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, membership_b = make_web_client("owner-b@example.com")

    client_a.post("/staff/new/", _staff_payload(name="Staff A"))
    client_b.post("/staff/new/", _staff_payload(name="Staff B"))

    response = client_a.get("/staff/")

    body = response.content.decode()
    assert "Staff A" in body
    assert "Staff B" not in body


def test_staff_created_by_one_salon_is_unreachable_from_another(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    client_a.post("/staff/new/", _staff_payload())
    staff = Staff.objects.get(salon=membership_a.salon)

    assert client_b.get(f"/staff/{staff.pk}/edit/").status_code == 404
    assert client_b.post(f"/staff/{staff.pk}/edit/", _staff_payload()).status_code == 404
    assert client_b.post(f"/staff/{staff.pk}/delete/").status_code == 404
    assert Staff.objects.filter(pk=staff.pk).exists()


def test_assign_services_to_staff(make_web_client):
    client, membership = make_web_client("owner@example.com")
    client.post("/staff/new/", _staff_payload())
    staff = Staff.objects.get(salon=membership.salon)
    service = _make_service(membership.salon)

    response = client.post(f"/staff/{staff.pk}/services/", {"services": [service.pk]})

    assert response.status_code == 302
    assert StaffService.objects.filter(staff=staff, service=service).exists()


def test_staff_service_assignment_rejects_a_service_from_another_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    _client_b, membership_b = make_web_client("owner-b@example.com")
    client_a.post("/staff/new/", _staff_payload())
    staff = Staff.objects.get(salon=membership_a.salon)
    other_salons_service = _make_service(membership_b.salon)

    response = client_a.post(
        f"/staff/{staff.pk}/services/", {"services": [other_salons_service.pk]}
    )

    assert response.status_code == 200
    assert not StaffService.objects.filter(staff=staff).exists()
