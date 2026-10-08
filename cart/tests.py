from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Product
from users.models import User

from .models import Cart, CartItem


class CartTests(APITestCase):
    cart_url = "/api/cart/"
    items_url = "/api/cart/items/"

    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Наушники")
        cls.product = Product.objects.create(
            category=category,
            name="JBL Tune 510BT",
            price=Decimal("620000"),
            stock=5,
        )
        cls.customer = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="Sup3rSecret!42"
        )
        cls.other = User.objects.create_user(
            username="other", email="other@example.com", password="Sup3rSecret!42"
        )

    def add_product(self, quantity=1):
        return self.client.post(
            self.items_url,
            {"product": self.product.id, "quantity": quantity},
            format="json",
        )

    def test_guest_has_no_cart(self):
        self.assertEqual(
            self.client.get(self.cart_url).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_cart_is_created_on_first_request(self):
        self.client.force_authenticate(self.customer)

        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])
        self.assertTrue(Cart.objects.filter(user=self.customer).exists())

    def test_add_product_and_count_total(self):
        self.client.force_authenticate(self.customer)

        response = self.add_product(quantity=2)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["items_count"], 2)
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("1240000.00"))

    def test_adding_same_product_increases_quantity(self):
        self.client.force_authenticate(self.customer)

        self.add_product(quantity=1)
        response = self.add_product(quantity=2)

        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 3)

    def test_cannot_add_more_than_stock(self):
        self.client.force_authenticate(self.customer)

        response = self.add_product(quantity=99)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_update_quantity_and_remove_item(self):
        self.client.force_authenticate(self.customer)
        self.add_product(quantity=1)
        item = CartItem.objects.get(cart__user=self.customer)

        response = self.client.patch(
            f"{self.items_url}{item.id}/", {"quantity": 4}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"][0]["quantity"], 4)

        response = self.client.delete(f"{self.items_url}{item.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_touch_someone_elses_cart_item(self):
        self.client.force_authenticate(self.other)
        self.add_product(quantity=1)
        foreign_item = CartItem.objects.get(cart__user=self.other)

        self.client.force_authenticate(self.customer)
        response = self.client.patch(
            f"{self.items_url}{foreign_item.id}/", {"quantity": 3}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        foreign_item.refresh_from_db()
        self.assertEqual(foreign_item.quantity, 1)

    def test_clear_cart(self):
        self.client.force_authenticate(self.customer)
        self.add_product(quantity=2)

        response = self.client.delete("/api/cart/clear/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(self.cart_url).data["items_count"], 0)
