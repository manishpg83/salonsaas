import pytest

from apps.catalog.models import Service, ServiceCategory
from apps.crm.models import Customer
from apps.scheduling.models import Appointment, AppointmentService
from apps.staff.models import Staff

pytestmark = pytest.mark.django_db


def _make_customer(salon, name="Kavya Reddy", mobile="9876500000"):
    return Customer.objects.create(salon=salon, name=name, mobile=mobile)


def _make_service(salon, name="Haircut", price="500.00", duration=30):
    category = ServiceCategory.objects.create(salon=salon, name=f"{name} category")
    return Service.objects.create(
        salon=salon, category=category, name=name, price=price, duration_minutes=duration
    )


def _make_staff(salon, name="Priya"):
    return Staff.objects.create(salon=salon, name=name, mobile="9111111111", joining_date="2025-01-01")


def _add_service(client, appointment, service, staff=None):
    return client.post(
        f"/appointments/{appointment.pk}/services/",
        {
            "services-TOTAL_FORMS": "1",
            "services-INITIAL_FORMS": "0",
            "services-MIN_NUM_FORMS": "0",
            "services-MAX_NUM_FORMS": "1000",
            "services-0-service": service.pk,
            "services-0-staff": staff.pk if staff else "",
        },
    )


def _appointment_payload(customer, **overrides):
    payload = {
        "customer": customer.pk,
        "branch": "",
        "date": "2026-09-01",
        "time": "10:00",
        "discount": "0",
        "advance": "0",
        "notes": "",
    }
    payload.update(overrides)
    return payload


def test_appointment_list_requires_login(client):
    response = client.get("/appointments/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_create_appointment_redirects_to_add_services(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)

    response = client.post("/appointments/new/", _appointment_payload(customer))

    assert response.status_code == 302
    appointment = Appointment.objects.get(salon=membership.salon)
    assert appointment.status == Appointment.Status.BOOKED
    assert response.url == f"/appointments/{appointment.pk}/services/"


def test_adding_services_recomputes_price_and_duration(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    haircut = _make_service(membership.salon, name="Haircut", price="500.00", duration=30)
    facial = _make_service(membership.salon, name="Facial", price="1200.00", duration=60)
    staff = _make_staff(membership.salon)
    client.post("/appointments/new/", _appointment_payload(customer))
    appointment = Appointment.objects.get(salon=membership.salon)

    formset_data = {
        "services-TOTAL_FORMS": "2",
        "services-INITIAL_FORMS": "0",
        "services-MIN_NUM_FORMS": "0",
        "services-MAX_NUM_FORMS": "1000",
        "services-0-service": haircut.pk,
        "services-0-staff": staff.pk,
        "services-1-service": facial.pk,
        "services-1-staff": "",
    }
    response = client.post(f"/appointments/{appointment.pk}/services/", formset_data)

    assert response.status_code == 302
    appointment.refresh_from_db()
    assert appointment.price == 1700
    assert appointment.duration_minutes == 90
    assert AppointmentService.objects.filter(appointment=appointment).count() == 2


def test_removing_a_service_line_recomputes_totals(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    haircut = _make_service(membership.salon, price="500.00", duration=30)
    client.post("/appointments/new/", _appointment_payload(customer))
    appointment = Appointment.objects.get(salon=membership.salon)
    client.post(
        f"/appointments/{appointment.pk}/services/",
        {
            "services-TOTAL_FORMS": "1",
            "services-INITIAL_FORMS": "0",
            "services-MIN_NUM_FORMS": "0",
            "services-MAX_NUM_FORMS": "1000",
            "services-0-service": haircut.pk,
            "services-0-staff": "",
        },
    )
    line = AppointmentService.objects.get(appointment=appointment)

    client.post(
        f"/appointments/{appointment.pk}/services/",
        {
            "services-TOTAL_FORMS": "1",
            "services-INITIAL_FORMS": "1",
            "services-MIN_NUM_FORMS": "0",
            "services-MAX_NUM_FORMS": "1000",
            "services-0-id": line.pk,
            "services-0-service": haircut.pk,
            "services-0-staff": "",
            "services-0-DELETE": "on",
        },
    )

    appointment.refresh_from_db()
    assert appointment.price == 0
    assert appointment.duration_minutes == 0
    assert not AppointmentService.objects.filter(appointment=appointment).exists()


def test_valid_status_chain_is_accepted(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    client.post("/appointments/new/", _appointment_payload(customer))
    appointment = Appointment.objects.get(salon=membership.salon)

    for status in ["CONFIRMED", "ARRIVED", "IN_SERVICE", "COMPLETED", "PAID"]:
        response = client.post(f"/appointments/{appointment.pk}/status/", {"status": status})
        assert response.status_code == 302
        appointment.refresh_from_db()
        assert appointment.status == status


def test_invalid_status_transition_is_rejected(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    client.post("/appointments/new/", _appointment_payload(customer))
    appointment = Appointment.objects.get(salon=membership.salon)

    response = client.post(f"/appointments/{appointment.pk}/status/", {"status": "PAID"})

    assert response.status_code == 302
    appointment.refresh_from_db()
    assert appointment.status == Appointment.Status.BOOKED


def test_terminal_status_cannot_transition_further(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    client.post("/appointments/new/", _appointment_payload(customer))
    appointment = Appointment.objects.get(salon=membership.salon)
    client.post(f"/appointments/{appointment.pk}/status/", {"status": "CANCELLED"})

    response = client.post(f"/appointments/{appointment.pk}/status/", {"status": "CONFIRMED"})

    assert response.status_code == 302
    appointment.refresh_from_db()
    assert appointment.status == Appointment.Status.CANCELLED


def test_create_detail_edit_and_services_pages_render(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)

    assert client.get("/appointments/new/").status_code == 200

    client.post("/appointments/new/", _appointment_payload(customer))
    appointment = Appointment.objects.get(salon=membership.salon)

    assert client.get(f"/appointments/{appointment.pk}/").status_code == 200
    assert client.get(f"/appointments/{appointment.pk}/edit/").status_code == 200
    assert client.get(f"/appointments/{appointment.pk}/services/").status_code == 200


def test_appointments_are_scoped_to_the_current_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, membership_b = make_web_client("owner-b@example.com")
    customer_a = _make_customer(membership_a.salon, name="Customer A", mobile="9111111111")
    customer_b = _make_customer(membership_b.salon, name="Customer B", mobile="9222222222")
    client_a.post("/appointments/new/", _appointment_payload(customer_a))
    client_b.post("/appointments/new/", _appointment_payload(customer_b))

    response = client_a.get("/appointments/", {"date": "2026-09-01"})

    body = response.content.decode()
    assert "Customer A" in body
    assert "Customer B" not in body


def test_appointment_created_by_one_salon_is_unreachable_from_another(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    customer_a = _make_customer(membership_a.salon)
    client_a.post("/appointments/new/", _appointment_payload(customer_a))
    appointment = Appointment.objects.get(salon=membership_a.salon)

    assert client_b.get(f"/appointments/{appointment.pk}/").status_code == 404
    assert client_b.get(f"/appointments/{appointment.pk}/edit/").status_code == 404
    assert client_b.post(f"/appointments/{appointment.pk}/delete/").status_code == 404
    assert client_b.post(f"/appointments/{appointment.pk}/status/", {"status": "CONFIRMED"}).status_code == 404
    assert Appointment.objects.filter(pk=appointment.pk).exists()


def test_appointment_form_rejects_a_customer_from_another_salon(make_web_client):
    client_a, _membership_a = make_web_client("owner-a@example.com")
    _client_b, membership_b = make_web_client("owner-b@example.com")
    other_salons_customer = _make_customer(membership_b.salon)

    response = client_a.post("/appointments/new/", _appointment_payload(other_salons_customer))

    assert response.status_code == 200
    assert "customer" in response.context["form"].errors
    assert not Appointment.objects.exists()


# --- 5.2: calendar filters -----------------------------------------------------


def test_day_view_shows_only_that_date(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-01"))
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-05"))

    response = client.get("/appointments/", {"view": "day", "date": "2026-09-01"})

    dates = [a.date.isoformat() for a in response.context["appointments"]]
    assert dates == ["2026-09-01"]


def test_week_view_shows_appointments_within_that_week_only(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    # 2026-09-01 falls in the Mon 2026-08-31 - Sun 2026-09-06 week.
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-08-31"))
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-06"))
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-07"))

    response = client.get("/appointments/", {"view": "week", "date": "2026-09-01"})

    dates = sorted(a.date.isoformat() for a in response.context["appointments"])
    assert dates == ["2026-08-31", "2026-09-06"]


def test_month_view_shows_appointments_within_that_month_only(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-01"))
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-30"))
    client.post("/appointments/new/", _appointment_payload(customer, date="2026-10-01"))

    response = client.get("/appointments/", {"view": "month", "date": "2026-09-15"})

    dates = sorted(a.date.isoformat() for a in response.context["appointments"])
    assert dates == ["2026-09-01", "2026-09-30"]


def test_filter_by_staff_and_status(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon)
    staff_a = _make_staff(membership.salon, name="Priya")
    staff_b = _make_staff(membership.salon, name="Anjali")

    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-01", time="09:00"))
    appt_a = Appointment.objects.get(customer=customer, time="09:00")
    _add_service(client, appt_a, service, staff_a)

    client.post("/appointments/new/", _appointment_payload(customer, date="2026-09-01", time="12:00"))
    appt_b = Appointment.objects.get(customer=customer, time="12:00")
    _add_service(client, appt_b, service, staff_b)
    client.post(f"/appointments/{appt_b.pk}/status/", {"status": "CONFIRMED"})

    by_staff = client.get("/appointments/", {"view": "day", "date": "2026-09-01", "staff": staff_a.pk})
    assert [a.pk for a in by_staff.context["appointments"]] == [appt_a.pk]

    by_status = client.get(
        "/appointments/", {"view": "day", "date": "2026-09-01", "status": "CONFIRMED"}
    )
    assert [a.pk for a in by_status.context["appointments"]] == [appt_b.pk]


# --- 5.2: staff double-booking conflicts ---------------------------------------


def test_overlapping_booking_for_the_same_staff_is_rejected(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer1 = _make_customer(membership.salon, name="Customer One", mobile="9111111111")
    customer2 = _make_customer(membership.salon, name="Customer Two", mobile="9222222222")
    service = _make_service(membership.salon, duration=60)
    staff = _make_staff(membership.salon)

    client.post("/appointments/new/", _appointment_payload(customer1, time="10:00"))
    appt1 = Appointment.objects.get(customer=customer1)
    _add_service(client, appt1, service, staff)

    client.post("/appointments/new/", _appointment_payload(customer2, time="10:30"))
    appt2 = Appointment.objects.get(customer=customer2)
    response = _add_service(client, appt2, service, staff)

    assert response.status_code == 200
    assert "already booked" in response.content.decode()
    assert not AppointmentService.objects.filter(appointment=appt2).exists()
    appt2.refresh_from_db()
    assert appt2.price == 0
    assert appt2.duration_minutes == 0


def test_back_to_back_bookings_for_the_same_staff_are_allowed(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer1 = _make_customer(membership.salon, name="Customer One", mobile="9111111111")
    customer2 = _make_customer(membership.salon, name="Customer Two", mobile="9222222222")
    service = _make_service(membership.salon, duration=60)
    staff = _make_staff(membership.salon)

    client.post("/appointments/new/", _appointment_payload(customer1, time="10:00"))
    appt1 = Appointment.objects.get(customer=customer1)
    _add_service(client, appt1, service, staff)

    client.post("/appointments/new/", _appointment_payload(customer2, time="11:00"))
    appt2 = Appointment.objects.get(customer=customer2)
    response = _add_service(client, appt2, service, staff)

    assert response.status_code == 302
    assert AppointmentService.objects.filter(appointment=appt2).exists()


def test_conflict_check_ignores_cancelled_appointments(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer1 = _make_customer(membership.salon, name="Customer One", mobile="9111111111")
    customer2 = _make_customer(membership.salon, name="Customer Two", mobile="9222222222")
    service = _make_service(membership.salon, duration=60)
    staff = _make_staff(membership.salon)

    client.post("/appointments/new/", _appointment_payload(customer1, time="10:00"))
    appt1 = Appointment.objects.get(customer=customer1)
    _add_service(client, appt1, service, staff)
    client.post(f"/appointments/{appt1.pk}/status/", {"status": "CANCELLED"})

    client.post("/appointments/new/", _appointment_payload(customer2, time="10:00"))
    appt2 = Appointment.objects.get(customer=customer2)
    response = _add_service(client, appt2, service, staff)

    assert response.status_code == 302
    assert AppointmentService.objects.filter(appointment=appt2).exists()


def test_editing_an_appointments_time_into_a_conflict_is_rejected(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer1 = _make_customer(membership.salon, name="Customer One", mobile="9111111111")
    customer2 = _make_customer(membership.salon, name="Customer Two", mobile="9222222222")
    service = _make_service(membership.salon, duration=60)
    staff = _make_staff(membership.salon)

    client.post("/appointments/new/", _appointment_payload(customer1, time="10:00"))
    appt1 = Appointment.objects.get(customer=customer1)
    _add_service(client, appt1, service, staff)

    client.post("/appointments/new/", _appointment_payload(customer2, time="14:00"))
    appt2 = Appointment.objects.get(customer=customer2)
    _add_service(client, appt2, service, staff)

    response = client.post(
        f"/appointments/{appt2.pk}/edit/", _appointment_payload(customer2, time="10:30")
    )

    assert response.status_code == 200
    assert "already booked" in response.content.decode()
    appt2.refresh_from_db()
    assert str(appt2.time) == "14:00:00"
