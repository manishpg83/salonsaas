from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.crm.models import Customer
from apps.messaging.models import Message, MessageTemplate
from apps.scheduling.models import Appointment

pytestmark = pytest.mark.django_db


def _customer(salon, **overrides):
    payload = {"name": "Kavya Reddy", "mobile": "9876500000"}
    payload.update(overrides)
    return Customer.objects.create(salon=salon, **payload)


def _appointment(salon, customer, date, status=Appointment.Status.BOOKED):
    return Appointment.objects.create(
        salon=salon, customer=customer, date=date, time="10:00", status=status
    )


def test_sends_a_reminder_for_an_appointment_tomorrow(make_web_client):
    _client, membership = make_web_client("owner@example.com")
    tomorrow = timezone.localdate() + timedelta(days=1)
    customer = _customer(membership.salon)
    appointment = _appointment(membership.salon, customer, tomorrow)

    call_command("send_appointment_reminders")

    message = Message.objects.get(salon=membership.salon, trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER)
    assert message.appointment == appointment
    assert message.customer == customer


def test_skips_an_appointment_that_is_not_tomorrow(make_web_client):
    _client, membership = make_web_client("owner@example.com")
    today = timezone.localdate()
    customer = _customer(membership.salon)
    _appointment(membership.salon, customer, today)

    call_command("send_appointment_reminders")

    assert not Message.objects.filter(
        salon=membership.salon, trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER
    ).exists()


def test_skips_a_cancelled_appointment(make_web_client):
    _client, membership = make_web_client("owner@example.com")
    tomorrow = timezone.localdate() + timedelta(days=1)
    customer = _customer(membership.salon)
    _appointment(membership.salon, customer, tomorrow, status=Appointment.Status.CANCELLED)

    call_command("send_appointment_reminders")

    assert not Message.objects.filter(
        salon=membership.salon, trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER
    ).exists()


def test_running_twice_does_not_send_a_duplicate_reminder(make_web_client):
    _client, membership = make_web_client("owner@example.com")
    tomorrow = timezone.localdate() + timedelta(days=1)
    customer = _customer(membership.salon)
    _appointment(membership.salon, customer, tomorrow)

    call_command("send_appointment_reminders")
    call_command("send_appointment_reminders")

    assert Message.objects.filter(
        salon=membership.salon, trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER
    ).count() == 1


def test_respects_a_disabled_reminder_template(make_web_client):
    _client, membership = make_web_client("owner@example.com")
    tomorrow = timezone.localdate() + timedelta(days=1)
    customer = _customer(membership.salon)
    _appointment(membership.salon, customer, tomorrow)
    MessageTemplate.objects.create(
        salon=membership.salon,
        trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER,
        body=MessageTemplate.DEFAULT_BODIES[MessageTemplate.Trigger.APPOINTMENT_REMINDER],
        is_active=False,
    )

    call_command("send_appointment_reminders")

    assert not Message.objects.filter(
        salon=membership.salon, trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER
    ).exists()


def test_reminders_are_scoped_to_their_own_salon(make_web_client):
    _client_a, membership_a = make_web_client("owner-a@example.com")
    _client_b, membership_b = make_web_client("owner-b@example.com")
    tomorrow = timezone.localdate() + timedelta(days=1)
    customer_a = _customer(membership_a.salon, name="Salon A Customer")
    customer_b = _customer(membership_b.salon, name="Salon B Customer", mobile="9222222222")
    _appointment(membership_a.salon, customer_a, tomorrow)
    _appointment(membership_b.salon, customer_b, tomorrow)

    call_command("send_appointment_reminders")

    assert Message.objects.filter(salon=membership_a.salon, customer=customer_a).exists()
    assert Message.objects.filter(salon=membership_b.salon, customer=customer_b).exists()
