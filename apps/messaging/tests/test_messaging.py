import pytest

from apps.crm.models import Customer
from apps.messaging.models import Message, MessageTemplate
from apps.messaging.providers import ConsoleProvider
from apps.messaging.services import render_body, send_message
from apps.salons.models import Role

pytestmark = pytest.mark.django_db


def _customer(salon, **overrides):
    payload = {"name": "Priya Shah", "mobile": "9876543210"}
    payload.update(overrides)
    return Customer.objects.create(salon=salon, **payload)


# --- providers / services (no HTTP) -----------------------------------------


def test_console_provider_sends_successfully(capsys):
    provider = ConsoleProvider()

    result = provider.send("9876543210", "Hello there")

    assert result is True
    assert "9876543210" in capsys.readouterr().out


def test_render_body_substitutes_placeholders():
    body = render_body(
        "Hi {{ customer_name }}, welcome to {{ salon_name }}.",
        {"customer_name": "Priya", "salon_name": "Glow Salon"},
    )

    assert body == "Hi Priya, welcome to Glow Salon."


def test_render_body_does_not_html_escape_special_characters():
    """This renders a plain-text WhatsApp message, not HTML — a salon name
    like "Glow & Co." must come through literally, not as "Glow &amp; Co."."""
    body = render_body(
        "Hi {{ customer_name }}, welcome to {{ salon_name }}.",
        {"customer_name": "O'Brien", "salon_name": "Glow & Co."},
    )

    assert body == "Hi O'Brien, welcome to Glow & Co.."


def test_send_message_logs_a_sent_message(make_web_client):
    _client, membership = make_web_client("owner@example.com")
    customer = _customer(membership.salon)

    message = send_message(
        salon=membership.salon,
        customer=customer,
        trigger=MessageTemplate.Trigger.BOOKING_CONFIRMATION,
        body="Your appointment is confirmed.",
    )

    assert message.status == Message.Status.SENT
    assert message.recipient == customer.mobile
    assert message.channel == Message.Channel.WHATSAPP
    assert Message.objects.filter(pk=message.pk).exists()


# --- template list / edit ----------------------------------------------------


def test_template_list_requires_login(client):
    response = client.get("/messaging/templates/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_owner_sees_one_auto_provisioned_row_per_trigger(make_web_client):
    client, membership = make_web_client("owner@example.com")

    response = client.get("/messaging/templates/")

    assert response.status_code == 200
    assert MessageTemplate.objects.filter(salon=membership.salon).count() == len(
        MessageTemplate.Trigger.choices
    )
    body = response.content.decode()
    for _trigger, label in MessageTemplate.Trigger.choices:
        assert label in body


def test_owner_can_edit_a_template(make_web_client):
    client, membership = make_web_client("owner@example.com")
    client.get("/messaging/templates/")  # provisions the rows
    template = MessageTemplate.objects.get(
        salon=membership.salon, trigger=MessageTemplate.Trigger.BOOKING_CONFIRMATION
    )

    response = client.post(
        f"/messaging/templates/{template.trigger}/edit/",
        {"body": "See you soon, {{ customer_name }}!", "is_active": ""},
    )

    assert response.status_code == 302
    template.refresh_from_db()
    assert template.body == "See you soon, {{ customer_name }}!"
    assert template.is_active is False


def test_receptionist_role_is_denied_template_management(make_web_client):
    client, membership = make_web_client("receptionist@example.com")
    membership.role = Role.RECEPTIONIST
    membership.save(update_fields=["role"])

    response = client.get("/messaging/templates/")

    assert response.status_code == 403


def test_templates_are_scoped_to_the_current_salon(make_web_client):
    """`trigger` is a fixed per-salon key, not a global pk (same pattern as
    Phase 3.2's StaffWorkingHours) — salon B visiting the same trigger's
    edit URL legitimately resolves to *its own* row, not a 404. The real
    isolation guarantee is that B never sees or can overwrite A's content."""
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    client_a.get("/messaging/templates/")  # provisions salon A's rows
    client_b.get("/messaging/templates/")  # provisions salon B's rows
    trigger = MessageTemplate.Trigger.BOOKING_CONFIRMATION
    template_a = MessageTemplate.objects.get(salon=membership_a.salon, trigger=trigger)
    template_a.body = "Salon A exclusive wording"
    template_a.save(update_fields=["body"])

    response = client_b.get(f"/messaging/templates/{trigger}/edit/")
    assert response.status_code == 200
    assert "Salon A exclusive wording" not in response.content.decode()

    client_b.post(f"/messaging/templates/{trigger}/edit/", {"body": "Salon B wording", "is_active": "on"})
    template_a.refresh_from_db()
    assert template_a.body == "Salon A exclusive wording"


# --- send-test action ---------------------------------------------------------


def test_owner_can_send_a_test_message_and_it_appears_in_the_log(make_web_client):
    client, membership = make_web_client("owner@example.com")
    client.get("/messaging/templates/")
    customer = _customer(membership.salon)
    trigger = MessageTemplate.Trigger.BOOKING_CONFIRMATION

    response = client.post(f"/messaging/templates/{trigger}/test/", {"customer": customer.pk})

    assert response.status_code == 302
    message = Message.objects.get(salon=membership.salon)
    assert message.customer == customer
    assert message.trigger == trigger
    assert message.status == Message.Status.SENT

    log_response = client.get("/messaging/log/")
    assert customer.name in log_response.content.decode()


def test_send_test_rejects_a_customer_from_another_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    _client_b, membership_b = make_web_client("owner-b@example.com")
    client_a.get("/messaging/templates/")
    foreign_customer = _customer(membership_b.salon, mobile="9111111111")
    trigger = MessageTemplate.Trigger.BOOKING_CONFIRMATION

    response = client_a.post(
        f"/messaging/templates/{trigger}/test/", {"customer": foreign_customer.pk}
    )

    assert response.status_code == 302
    assert not Message.objects.filter(salon=membership_a.salon).exists()


# --- message log ---------------------------------------------------------------


def test_message_log_is_open_to_every_salon_role(make_web_client):
    client, membership = make_web_client("receptionist@example.com")
    membership.role = Role.RECEPTIONIST
    membership.save(update_fields=["role"])
    customer = _customer(membership.salon)
    send_message(
        salon=membership.salon,
        customer=customer,
        trigger=MessageTemplate.Trigger.FEEDBACK_REQUEST,
        body="Thanks for visiting!",
    )

    response = client.get("/messaging/log/")

    assert response.status_code == 200
    assert customer.name in response.content.decode()


def test_message_log_is_scoped_to_the_current_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    _client_b, membership_b = make_web_client("owner-b@example.com")
    customer_a = _customer(membership_a.salon, name="Salon A Customer")
    customer_b = _customer(membership_b.salon, name="Salon B Customer", mobile="9222222222")
    send_message(
        salon=membership_a.salon,
        customer=customer_a,
        trigger=MessageTemplate.Trigger.FEEDBACK_REQUEST,
        body="Thanks!",
    )
    send_message(
        salon=membership_b.salon,
        customer=customer_b,
        trigger=MessageTemplate.Trigger.FEEDBACK_REQUEST,
        body="Thanks!",
    )

    response = client_a.get("/messaging/log/")

    body = response.content.decode()
    assert "Salon A Customer" in body
    assert "Salon B Customer" not in body
