import pytest

from apps.catalog.models import Service, ServiceCategory
from apps.inventory.models import (
    Product,
    ProductCategory,
    Purchase,
    ServiceProduct,
    StockTransaction,
    Supplier,
)
from apps.salons.models import Role

pytestmark = pytest.mark.django_db


def _product_payload(**overrides):
    payload = {
        "name": "Shampoo 250ml",
        "sku": "SH-250",
        "category": "",
        "supplier": "",
        "purchase_price": "120.00",
        "selling_price": "200.00",
        "min_stock": "5",
        "expiry_date": "",
        "is_active": "on",
    }
    payload.update(overrides)
    return payload


def _make_product(salon, name="Shampoo 250ml", sku="SH-250", min_stock=5):
    return Product.objects.create(salon=salon, name=name, sku=sku, min_stock=min_stock)


def test_product_list_requires_login(client):
    response = client.get("/products/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_owner_can_create_list_edit_and_delete_product(make_web_client):
    client, membership = make_web_client("owner@example.com")

    create = client.post("/products/new/", _product_payload())
    assert create.status_code == 302
    product = Product.objects.get(salon=membership.salon)
    assert product.name == "Shampoo 250ml"
    assert product.current_stock == 0  # opening stock is always 0 — added via purchase/adjust

    list_response = client.get("/products/")
    assert list_response.status_code == 200
    assert "Shampoo 250ml" in list_response.content.decode()

    edit = client.post(f"/products/{product.pk}/edit/", _product_payload(name="Shampoo 400ml"))
    assert edit.status_code == 302
    product.refresh_from_db()
    assert product.name == "Shampoo 400ml"

    delete = client.post(f"/products/{product.pk}/delete/")
    assert delete.status_code == 302
    assert not Product.objects.filter(pk=product.pk).exists()


def test_receptionist_role_is_denied_inventory_access(make_web_client):
    client, membership = make_web_client("receptionist@example.com")
    membership.role = Role.RECEPTIONIST
    membership.save(update_fields=["role"])

    response = client.get("/products/")

    assert response.status_code == 403


def test_recording_a_purchase_brings_stock_in(make_web_client):
    client, membership = make_web_client("owner@example.com")
    product = _make_product(membership.salon)
    supplier = Supplier.objects.create(salon=membership.salon, name="Beauty Distributors")

    create = client.post(
        "/purchases/new/", {"supplier": supplier.pk, "date": "2026-09-01", "notes": ""}
    )
    assert create.status_code == 302
    purchase = Purchase.objects.get(salon=membership.salon)

    response = client.post(
        f"/purchases/{purchase.pk}/items/",
        {"product": product.pk, "quantity": "20", "unit_cost": "110.00"},
    )

    assert response.status_code == 302
    product.refresh_from_db()
    purchase.refresh_from_db()
    assert product.current_stock == 20
    assert purchase.total == 2200
    txn = StockTransaction.objects.get(product=product)
    assert txn.type == StockTransaction.Type.IN
    assert txn.quantity == 20


def test_manual_stock_adjustment_changes_current_stock(make_web_client):
    client, membership = make_web_client("owner@example.com")
    product = _make_product(membership.salon)

    response = client.post(
        f"/products/{product.pk}/adjust/", {"quantity": "-3", "reason": "Damaged bottle"}
    )

    assert response.status_code == 302
    product.refresh_from_db()
    assert product.current_stock == -3
    txn = StockTransaction.objects.get(product=product)
    assert txn.type == StockTransaction.Type.ADJUST
    assert txn.quantity == -3
    assert txn.reference == "Damaged bottle"


def test_low_stock_flag(make_web_client):
    client, membership = make_web_client("owner@example.com")
    low = _make_product(membership.salon, name="Low", sku="LOW-1", min_stock=10)
    healthy = _make_product(membership.salon, name="Healthy", sku="HEALTHY-1", min_stock=2)
    client.post(f"/products/{low.pk}/adjust/", {"quantity": "5", "reason": "opening stock"})
    client.post(f"/products/{healthy.pk}/adjust/", {"quantity": "5", "reason": "opening stock"})
    low.refresh_from_db()
    healthy.refresh_from_db()

    assert low.is_low_stock  # 5 <= 10
    assert not healthy.is_low_stock  # 5 > 2

    response = client.get("/products/")
    assert "Low stock" in response.content.decode()


def test_products_are_scoped_to_the_current_salon(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, membership_b = make_web_client("owner-b@example.com")
    _make_product(membership_a.salon, name="Salon A Product", sku="A-1")

    response = client_b.get("/products/")

    assert "Salon A Product" not in response.content.decode()


def test_product_from_another_salon_is_unreachable(make_web_client):
    client_a, membership_a = make_web_client("owner-a@example.com")
    client_b, _membership_b = make_web_client("owner-b@example.com")
    product = _make_product(membership_a.salon)

    assert client_b.get(f"/products/{product.pk}/").status_code == 404
    assert client_b.post(f"/products/{product.pk}/edit/", _product_payload()).status_code == 404
    assert (
        client_b.post(f"/products/{product.pk}/adjust/", {"quantity": "1", "reason": ""}).status_code
        == 404
    )


def _make_service(salon, name="Haircut"):
    category = ServiceCategory.objects.create(salon=salon, name=f"{name} category")
    return Service.objects.create(salon=salon, category=category, name=name, price="500.00", duration_minutes=30)


def test_owner_can_add_and_remove_a_consumption_recipe(make_web_client):
    client, membership = make_web_client("owner@example.com")
    product = _make_product(membership.salon)
    service = _make_service(membership.salon)

    response = client.post(f"/products/{product.pk}/recipe/", {"service": service.pk, "quantity": "2"})

    assert response.status_code == 302
    recipe = ServiceProduct.objects.get(product=product, service=service)
    assert recipe.quantity == 2

    detail = client.get(f"/products/{product.pk}/").content.decode()
    assert "Haircut" in detail

    delete = client.post(f"/products/{product.pk}/recipe/{recipe.pk}/delete/")
    assert delete.status_code == 302
    assert not ServiceProduct.objects.filter(pk=recipe.pk).exists()


def test_adding_a_recipe_for_the_same_service_updates_quantity_instead_of_duplicating(make_web_client):
    client, membership = make_web_client("owner@example.com")
    product = _make_product(membership.salon)
    service = _make_service(membership.salon)

    client.post(f"/products/{product.pk}/recipe/", {"service": service.pk, "quantity": "2"})
    client.post(f"/products/{product.pk}/recipe/", {"service": service.pk, "quantity": "5"})

    assert ServiceProduct.objects.filter(product=product, service=service).count() == 1
    assert ServiceProduct.objects.get(product=product, service=service).quantity == 5


def test_owner_can_manage_suppliers_and_categories(make_web_client):
    client, membership = make_web_client("owner@example.com")

    supplier_create = client.post(
        "/suppliers/new/",
        {"name": "Glow Supplies", "contact_phone": "", "contact_email": "", "address": "", "notes": ""},
    )
    assert supplier_create.status_code == 302
    assert Supplier.objects.filter(salon=membership.salon, name="Glow Supplies").exists()

    category_create = client.post("/product-categories/new/", {"name": "Hair care"})
    assert category_create.status_code == 302
    assert ProductCategory.objects.filter(salon=membership.salon, name="Hair care").exists()
