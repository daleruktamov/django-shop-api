from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from catalog.models import Category, Product
from users.models import User

from .models import Order


class OrderTests(APITestCase):
    url = "/api/orders/"

    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Смартфоны")
        cls.product = Product.objects.create(
            category=category,
            name="Samsung Galaxy A55",
            price=Decimal("4200000"),
            stock=10,
        )
        cls.customer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="Sup3rSecret!42",
            phone="+998901112233",
            address="Ташкент, Чиланзар",
        )
        cls.other = User.objects.create_user(
            username="other", email="other@example.com", password="Sup3rSecret!42"
        )
        cls.admin = User.objects.create_superuser(
            username="boss", email="boss@example.com", password="Sup3rSecret!42"
        )

    def fill_cart(self, user=None, quantity=2):
        cart, _ = Cart.objects.get_or_create(user=user or self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=quantity)
        return cart

    def test_guest_cannot_create_order(self):
        self.assertEqual(
            self.client.post(self.url, {}, format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_empty_cart_cannot_become_order(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_moves_cart_into_order(self):
        self.fill_cart(quantity=2)
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("8400000.00"))
        self.assertEqual(response.data["status"], Order.Status.NEW)
        # Корзина очищена, склад уменьшился.
        self.assertEqual(CartItem.objects.filter(cart__user=self.customer).count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(self.product.sold_count, 2)

    def test_delivery_data_is_taken_from_profile(self):
        self.fill_cart(quantity=1)
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.data["address"], "Ташкент, Чиланзар")
        self.assertEqual(response.data["phone"], "+998901112233")

    def test_address_is_required_when_profile_is_empty(self):
        self.fill_cart(user=self.other, quantity=1)
        self.client.force_authenticate(self.other)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("address", response.data)

    def test_price_is_frozen_at_purchase_time(self):
        self.fill_cart(quantity=1)
        self.client.force_authenticate(self.customer)
        order_id = self.client.post(self.url, {}, format="json").data["id"]

        self.product.price = Decimal("9999999")
        self.product.save(update_fields=["price"])

        response = self.client.get(f"{self.url}{order_id}/")

        self.assertEqual(Decimal(response.data["items"][0]["price"]), Decimal("4200000.00"))
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("4200000.00"))

    def test_cannot_order_more_than_stock(self):
        self.fill_cart(quantity=3)
        self.product.stock = 1
        self.product.save(update_fields=["stock"])
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_user_sees_only_own_orders(self):
        self.fill_cart(quantity=1)
        self.client.force_authenticate(self.customer)
        order_id = self.client.post(self.url, {}, format="json").data["id"]

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url).data["count"], 0)
        self.assertEqual(
            self.client.get(f"{self.url}{order_id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_admin_sees_all_orders_and_changes_status(self):
        self.fill_cart(quantity=1)
        self.client.force_authenticate(self.customer)
        order_id = self.client.post(self.url, {}, format="json").data["id"]

        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.url).data["count"], 1)

        response = self.client.patch(
            f"{self.url}{order_id}/status/",
            {"status": Order.Status.SHIPPED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.SHIPPED)

    def test_customer_cannot_change_status(self):
        self.fill_cart(quantity=1)
        self.client.force_authenticate(self.customer)
        order_id = self.client.post(self.url, {}, format="json").data["id"]

        response = self.client.patch(
            f"{self.url}{order_id}/status/",
            {"status": Order.Status.DELIVERED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_returns_products_to_stock(self):
        self.fill_cart(quantity=2)
        self.client.force_authenticate(self.customer)
        order_id = self.client.post(self.url, {}, format="json").data["id"]

        response = self.client.post(f"{self.url}{order_id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_delivered_order_cannot_be_cancelled(self):
        self.fill_cart(quantity=1)
        self.client.force_authenticate(self.customer)
        order_id = self.client.post(self.url, {}, format="json").data["id"]
        Order.objects.filter(pk=order_id).update(status=Order.Status.DELIVERED)

        response = self.client.post(f"{self.url}{order_id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
