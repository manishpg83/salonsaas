import pytest

from apps.catalog.models import Service, ServiceCategory
from apps.crm.models import Customer
from apps.inventory.models import Product, ServiceProduct, StockTransaction
from apps.scheduling.models import Appointment

pytestmark = pytest.mark.django_db


def _make_customer(salon, name="Kavya Reddy", mobile="9876500000"):
    return Customer.objects.create(salon=salon, name=name, mobile=mobile)


def _make_service(salon, name="Haircut", price="500.00", duration=30):
    category = ServiceCategory.objects.create(salon=salon, name=f"{name} category")
    return Service.objects.create(
        salon=salon, category=category, name=name, price=price, duration_minutes=duration
    )


def _make_product(salon, name="Shampoo 250ml", sku="SH-250"):
    return Product.objects.create(salon=salon, name=name, sku=sku, min_stock=0)


def _booked_appointment(client, salon, customer, service):
    client.post(
        "/appointments/new/",
        {
            "customer": customer.pk, "branch": "", "date": "2026-09-01", "time": "10:00",
            "discount": "0", "advance": "0", "notes": "",
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
    return appointment


def _advance_to(client, appointment, statuses):
    for status in statuses:
        client.post(f"/appointments/{appointment.pk}/status/", {"status": status})
    appointment.refresh_from_db()
    return appointment


def test_completing_an_appointment_deducts_recipe_stock(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon)
    product = _make_product(membership.salon)
    ServiceProduct.objects.create(salon=membership.salon, service=service, product=product, quantity=3)
    # Give the product some opening stock to consume from.
    client.post(f"/products/{product.pk}/adjust/", {"quantity": "10", "reason": "opening stock"})

    appointment = _booked_appointment(client, membership.salon, customer, service)
    _advance_to(client, appointment, ["CONFIRMED", "ARRIVED", "IN_SERVICE", "COMPLETED"])

    product.refresh_from_db()
    assert product.current_stock == 7  # 10 - 3
    out_txn = StockTransaction.objects.get(product=product, type=StockTransaction.Type.OUT)
    assert out_txn.quantity == -3
    assert f"Appointment #{appointment.pk}" in out_txn.reference


def test_completing_an_appointment_without_a_recipe_leaves_stock_unchanged(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon)
    product = _make_product(membership.salon)
    client.post(f"/products/{product.pk}/adjust/", {"quantity": "10", "reason": "opening stock"})

    appointment = _booked_appointment(client, membership.salon, customer, service)
    _advance_to(client, appointment, ["CONFIRMED", "ARRIVED", "IN_SERVICE", "COMPLETED"])

    product.refresh_from_db()
    assert product.current_stock == 10
    assert not StockTransaction.objects.filter(product=product, type=StockTransaction.Type.OUT).exists()


def test_completing_an_appointment_twice_does_not_double_deduct(make_web_client):
    client, membership = make_web_client("owner@example.com")
    customer = _make_customer(membership.salon)
    service = _make_service(membership.salon)
    product = _make_product(membership.salon)
    ServiceProduct.objects.create(salon=membership.salon, service=service, product=product, quantity=3)
    client.post(f"/products/{product.pk}/adjust/", {"quantity": "10", "reason": "opening stock"})

    appointment = _booked_appointment(client, membership.salon, customer, service)
    _advance_to(client, appointment, ["CONFIRMED", "ARRIVED", "IN_SERVICE", "COMPLETED"])

    # Try to "complete" again — the status machine forbids COMPLETED -> COMPLETED,
    # so this should be rejected and must not deduct stock a second time.
    second_attempt = client.post(f"/appointments/{appointment.pk}/status/", {"status": "COMPLETED"})
    assert second_attempt.status_code == 302

    product.refresh_from_db()
    appointment.refresh_from_db()
    assert appointment.status == Appointment.Status.COMPLETED
    assert product.current_stock == 7  # still just one deduction
    assert StockTransaction.objects.filter(product=product, type=StockTransaction.Type.OUT).count() == 1
