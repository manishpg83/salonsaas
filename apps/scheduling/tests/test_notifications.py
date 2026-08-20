import pytest

from apps.catalog.models import Service, ServiceCategory
from apps.crm.models import Customer
from apps.messaging.models import Message, MessageTemplate
from apps.scheduling.models import Appointment

pytestmark = pytest.mark.django_db


def _make_customer(salon, name="Kavya Reddy", mobile="9876500000"):
    return Customer.objects.create(salon=salon, name=name, mobile=mobile)


def _make_service(salon, name="Haircut", price="500.00", duration=30):
    category = ServiceCategory.objects.create(salon=salon, name=f"{name} category")
    return Service.objects.create(
        salon=salon, category=category, name=name, price=price, duration_minutes=duration
    )


def _book(client, salon, customer, date="2026-09-01", time="10:00"):
    client.post(
        "/appointments/new/",
        {
            "customer": customer.pk, "branch": "", "date": date, "time": time,
            "discount": "0", "advance": "0", "notes": "",
        },
    )
    return Appointment.objects.get(salon=salon, customer=customer)


def _add_service(client, appointment, service):
    client.post(
        f"/appointments/{appointment.pk}/services/",
        {
            "services-TOTAL_FORMS": "1",
            "services-INITIAL_FORMS": "0",
            "services-MIN_NUM_FORMS": "0",
            "services-MAX_NUM_FORMS": "1000",
            "services-0-service": service.pk,
            "services-0-staff": "",
        },
    )


def _advance_to(client, appointment, statuses):
    for status in statuses:
        client.post(f"/appointments/{appointment.pk}/status/", {"status": status})
    appointment.refresh_from_db()
    return appointment


def test_booking_an_appointment_sends_a_confirmation_message(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)

    appointment = _book(client, membership.salon, customer)

    message = Message.objects.get(salon=membership.salon, trigger=MessageTemplate.Trigger.BOOKING_CONFIRMATION)
    assert message.customer == customer
    assert message.appointment == appointment
    assert message.status == Message.Status.SENT
    assert customer.name in message.body


def test_completing_an_appointment_sends_a_feedback_request(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon)
    appointment = _book(client, membership.salon, customer)
    _add_service(client, appointment, service)

    _advance_to(client, appointment, ["CONFIRMED", "ARRIVED", "IN_SERVICE", "COMPLETED"])

    assert Message.objects.filter(
        salon=membership.salon, appointment=appointment, trigger=MessageTemplate.Trigger.FEEDBACK_REQUEST
    ).exists()


def test_cancelling_an_appointment_sends_a_cancellation_notice(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    appointment = _book(client, membership.salon, customer)

    _advance_to(client, appointment, ["CANCELLED"])

    assert Message.objects.filter(
        salon=membership.salon, appointment=appointment, trigger=MessageTemplate.Trigger.CANCELLATION_NOTICE
    ).exists()


def test_arriving_does_not_send_any_message(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    appointment = _book(client, membership.salon, customer)
    Message.objects.filter(salon=membership.salon).delete()  # clear the booking confirmation

    _advance_to(client, appointment, ["CONFIRMED", "ARRIVED"])

    assert not Message.objects.filter(salon=membership.salon, appointment=appointment).exists()


def test_rescheduling_an_appointment_sends_a_notice(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    appointment = _book(client, membership.salon, customer)
    Message.objects.filter(salon=membership.salon).delete()  # clear the booking confirmation

    response = client.post(
        f"/appointments/{appointment.pk}/edit/",
        {
            "customer": customer.pk, "branch": "", "date": "2026-09-02", "time": "11:00",
            "discount": "0", "advance": "0", "notes": "",
        },
    )

    assert response.status_code == 302
    assert Message.objects.filter(
        salon=membership.salon, appointment=appointment, trigger=MessageTemplate.Trigger.CANCELLATION_NOTICE
    ).exists()


def test_editing_without_changing_date_or_time_sends_no_notice(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    appointment = _book(client, membership.salon, customer)
    Message.objects.filter(salon=membership.salon).delete()  # clear the booking confirmation

    response = client.post(
        f"/appointments/{appointment.pk}/edit/",
        {
            "customer": customer.pk, "branch": "", "date": "2026-09-01", "time": "10:00",
            "discount": "0", "advance": "50", "notes": "changed the advance only",
        },
    )

    assert response.status_code == 302
    assert not Message.objects.filter(salon=membership.salon, appointment=appointment).exists()


def test_disabling_a_trigger_suppresses_its_automatic_message(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    MessageTemplate.objects.create(
        salon=membership.salon,
        trigger=MessageTemplate.Trigger.BOOKING_CONFIRMATION,
        body=MessageTemplate.DEFAULT_BODIES[MessageTemplate.Trigger.BOOKING_CONFIRMATION],
        is_active=False,
    )

    _book(client, membership.salon, customer)

    assert not Message.objects.filter(
        salon=membership.salon, trigger=MessageTemplate.Trigger.BOOKING_CONFIRMATION
    ).exists()
