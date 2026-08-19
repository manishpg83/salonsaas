import pytest

from apps.billing.models import Invoice
from apps.catalog.models import Service, ServiceCategory
from apps.crm.models import Customer
from apps.scheduling.models import Appointment

pytestmark = pytest.mark.django_db


def _make_customer(salon, name="Kavya Reddy", mobile="9876500000"):
    return Customer.objects.create(salon=salon, name=name, mobile=mobile)


def _make_service(salon, name="Haircut", price="500.00", tax_percent="10.00", duration=30):
    category = ServiceCategory.objects.create(salon=salon, name=f"{name} category")
    return Service.objects.create(
        salon=salon,
        category=category,
        name=name,
        price=price,
        tax_percent=tax_percent,
        duration_minutes=duration,
    )


def _completed_appointment(client, salon, customer, service, discount="0"):
    """Books an appointment, adds one service line, and walks it through the
    status flow to COMPLETED — the only state a Phase 6.1 invoice can be
    generated from."""
    client.post(
        "/appointments/new/",
        {
            "customer": customer.pk,
            "branch": "",
            "date": "2026-09-01",
            "time": "10:00",
            "discount": discount,
            "advance": "0",
            "notes": "",
        },
    )
    appointment = Appointment.objects.get(salon=salon, customer=customer)
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
    for status in ["CONFIRMED", "ARRIVED", "IN_SERVICE", "COMPLETED"]:
        client.post(f"/appointments/{appointment.pk}/status/", {"status": status})
    appointment.refresh_from_db()
    return appointment


def test_invoice_list_requires_login(client):
    response = client.get("/invoices/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_generate_invoice_computes_correct_totals(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon, price="500.00", tax_percent="10.00")
    appointment = _completed_appointment(client, membership.salon, customer, service)

    response = client.post(f"/appointments/{appointment.pk}/invoice/")

    assert response.status_code == 302
    invoice = Invoice.objects.get(appointment=appointment)
    assert invoice.subtotal == 500
    assert invoice.tax_total == 50
    assert invoice.discount == 0
    assert invoice.total == 550
    assert invoice.items.count() == 1


def test_generate_invoice_snapshots_the_appointments_discount(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon, price="500.00", tax_percent="0")
    appointment = _completed_appointment(client, membership.salon, customer, service, discount="50")

    client.post(f"/appointments/{appointment.pk}/invoice/")

    invoice = Invoice.objects.get(appointment=appointment)
    assert invoice.discount == 50
    assert invoice.total == 450


def test_cannot_generate_invoice_for_a_non_completed_appointment(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    client.post(
        "/appointments/new/",
        {
            "customer": customer.pk, "branch": "", "date": "2026-09-01", "time": "10:00",
            "discount": "0", "advance": "0", "notes": "",
        },
    )
    appointment = Appointment.objects.get(salon=membership.salon, customer=customer)

    response = client.post(f"/appointments/{appointment.pk}/invoice/")

    assert response.status_code == 302
    assert not Invoice.objects.exists()


def test_generating_twice_redirects_to_the_existing_invoice(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon)
    appointment = _completed_appointment(client, membership.salon, customer, service)
    client.post(f"/appointments/{appointment.pk}/invoice/")
    invoice = Invoice.objects.get(appointment=appointment)

    response = client.post(f"/appointments/{appointment.pk}/invoice/")

    assert response.status_code == 302
    assert response.url == f"/invoices/{invoice.pk}/"
    assert Invoice.objects.filter(appointment=appointment).count() == 1


def test_adding_an_ad_hoc_item_recomputes_totals(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon, price="500.00", tax_percent="0")
    appointment = _completed_appointment(client, membership.salon, customer, service)
    client.post(f"/appointments/{appointment.pk}/invoice/")
    invoice = Invoice.objects.get(appointment=appointment)

    response = client.post(
        f"/invoices/{invoice.pk}/items/",
        {"description": "Hair serum", "quantity": "2", "unit_price": "150.00", "tax_percent": "0"},
    )

    assert response.status_code == 302
    invoice.refresh_from_db()
    assert invoice.items.count() == 2
    assert invoice.subtotal == 800  # 500 (service) + 2 x 150 (product)
    assert invoice.total == 800


def test_updating_discount_recomputes_total(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon, price="500.00", tax_percent="0")
    appointment = _completed_appointment(client, membership.salon, customer, service)
    client.post(f"/appointments/{appointment.pk}/invoice/")
    invoice = Invoice.objects.get(appointment=appointment)

    response = client.post(f"/invoices/{invoice.pk}/discount/", {"discount": "50"})

    assert response.status_code == 302
    invoice.refresh_from_db()
    assert invoice.discount == 50
    assert invoice.total == 450


def test_split_payment_summing_to_total_marks_appointment_paid(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon, price="500.00", tax_percent="0")
    appointment = _completed_appointment(client, membership.salon, customer, service)
    client.post(f"/appointments/{appointment.pk}/invoice/")
    invoice = Invoice.objects.get(appointment=appointment)

    client.post(f"/invoices/{invoice.pk}/payments/", {"method": "CASH", "amount": "300", "reference": ""})
    invoice.refresh_from_db()
    appointment.refresh_from_db()
    assert invoice.paid_total == 300
    assert not invoice.is_fully_paid
    assert appointment.status == Appointment.Status.COMPLETED

    client.post(f"/invoices/{invoice.pk}/payments/", {"method": "UPI", "amount": "200", "reference": "txn123"})
    invoice.refresh_from_db()
    appointment.refresh_from_db()
    assert invoice.paid_total == 500
    assert invoice.is_fully_paid
    assert appointment.status == Appointment.Status.PAID


def test_invoice_detail_and_appointment_detail_pages_render(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon)
    appointment = _completed_appointment(client, membership.salon, customer, service)

    still_no_invoice = client.get(f"/appointments/{appointment.pk}/")
    assert still_no_invoice.status_code == 200
    assert "Generate invoice" in still_no_invoice.content.decode()

    client.post(f"/appointments/{appointment.pk}/invoice/")
    invoice = Invoice.objects.get(appointment=appointment)

    detail = client.get(f"/invoices/{invoice.pk}/")
    assert detail.status_code == 200
    assert invoice.invoice_number in detail.content.decode()

    with_invoice = client.get(f"/appointments/{appointment.pk}/")
    assert invoice.invoice_number in with_invoice.content.decode()


def test_invoices_are_scoped_to_the_current_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, membership_b = make_web_client("owner-b@example.com")
    customer_a = _make_customer(membership_a.salon, name="Customer A", mobile="9111111111")
    service_a = _make_service(membership_a.salon)
    appointment_a = _completed_appointment(client_a, membership_a.salon, customer_a, service_a)
    client_a.post(f"/appointments/{appointment_a.pk}/invoice/")

    response = client_b.get("/invoices/")

    assert "Customer A" not in response.content.decode()


def test_invoice_created_in_one_salon_is_unreachable_from_another(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    customer_a = _make_customer(membership_a.salon)
    service_a = _make_service(membership_a.salon)
    appointment_a = _completed_appointment(client_a, membership_a.salon, customer_a, service_a)
    client_a.post(f"/appointments/{appointment_a.pk}/invoice/")
    invoice = Invoice.objects.get(appointment=appointment_a)

    assert client_b.get(f"/invoices/{invoice.pk}/").status_code == 404
    assert client_b.post(f"/invoices/{invoice.pk}/discount/", {"discount": "10"}).status_code == 404
    assert (
        client_b.post(
            f"/invoices/{invoice.pk}/payments/", {"method": "CASH", "amount": "1", "reference": ""}
        ).status_code
        == 404
    )
