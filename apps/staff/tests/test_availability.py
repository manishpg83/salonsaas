import datetime

import pytest

from apps.catalog.models import Service, ServiceCategory
from apps.staff.models import Staff, StaffService, StaffWorkingHours

pytestmark = pytest.mark.django_db


def _make_service(salon, name="Haircut"):
    category = ServiceCategory.objects.create(salon=salon, name="Hair")
    return Service.objects.create(
        salon=salon, category=category, name=name, price="500.00", duration_minutes=30
    )


def _make_staff(salon, name="Priya"):
    return Staff.objects.create(salon=salon, name=name, mobile="9999999999", joining_date="2026-01-01")


def test_visiting_the_hours_page_provisions_all_seven_weekdays(make_web_client):
    client, membership = make_web_client("owner@example.com")
    staff = _make_staff(membership.salon)

    response = client.get(f"/staff/{staff.pk}/hours/")

    assert response.status_code == 200
    rows = StaffWorkingHours.objects.filter(staff=staff)
    assert rows.count() == 7
    assert all(row.is_off for row in rows)


def test_owner_can_set_working_hours(make_web_client):
    client, membership = make_web_client("owner@example.com")
    staff = _make_staff(membership.salon)
    client.get(f"/staff/{staff.pk}/hours/")  # provisions the 7 rows

    formset_data = {
        "form-TOTAL_FORMS": "7",
        "form-INITIAL_FORMS": "7",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "7",
    }
    for i, row in enumerate(StaffWorkingHours.objects.filter(staff=staff).order_by("weekday")):
        is_monday_to_friday = row.weekday <= 4
        formset_data[f"form-{i}-id"] = row.pk
        formset_data[f"form-{i}-start_time"] = "09:00" if is_monday_to_friday else ""
        formset_data[f"form-{i}-end_time"] = "18:00" if is_monday_to_friday else ""
        if is_monday_to_friday:
            pass  # is_off omitted => False (an unchecked checkbox sends nothing)
        else:
            formset_data[f"form-{i}-is_off"] = "on"

    response = client.post(f"/staff/{staff.pk}/hours/", formset_data)

    assert response.status_code == 302
    monday = StaffWorkingHours.objects.get(staff=staff, weekday=0)
    assert monday.is_off is False
    assert str(monday.start_time) == "09:00:00"
    saturday = StaffWorkingHours.objects.get(staff=staff, weekday=5)
    assert saturday.is_off is True


def _set_monday_to_friday_hours(staff):
    for weekday in range(7):
        StaffWorkingHours.objects.update_or_create(
            staff=staff,
            weekday=weekday,
            defaults={"salon": staff.salon, "is_off": weekday > 4, "start_time": "09:00", "end_time": "18:00"},
        )


def test_availability_lookup_returns_staff_who_can_do_the_service_and_are_scheduled(make_web_client):
    client, membership = make_web_client("owner@example.com")
    service = _make_service(membership.salon)
    working_staff = _make_staff(membership.salon, name="Priya")
    _set_monday_to_friday_hours(working_staff)
    StaffService.objects.create(salon=membership.salon, staff=working_staff, service=service)

    off_on_that_day_staff = _make_staff(membership.salon, name="Rani")
    _set_monday_to_friday_hours(off_on_that_day_staff)
    StaffService.objects.create(salon=membership.salon, staff=off_on_that_day_staff, service=service)

    cant_do_service_staff = _make_staff(membership.salon, name="Anjali")
    _set_monday_to_friday_hours(cant_do_service_staff)

    monday = datetime.date(2026, 8, 24)
    saturday = datetime.date(2026, 8, 29)
    assert monday.weekday() == 0
    assert saturday.weekday() == 5

    response = client.get(
        "/staff/availability/", {"service": service.pk, "date": monday.isoformat()}
    )
    names = [s.name for s in response.context["free_staff"]]
    assert names == ["Priya", "Rani"]

    saturday_response = client.get(
        "/staff/availability/", {"service": service.pk, "date": saturday.isoformat()}
    )
    assert list(saturday_response.context["free_staff"]) == []


def test_availability_lookup_rejects_a_service_from_another_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    _client_b, membership_b = make_web_client("owner-b@example.com")
    other_salons_service = _make_service(membership_b.salon)

    response = client_a.get(
        "/staff/availability/", {"service": other_salons_service.pk, "date": "2026-08-24"}
    )

    assert response.status_code == 200
    assert response.context["free_staff"] is None
    assert "service" in response.context["form"].errors
