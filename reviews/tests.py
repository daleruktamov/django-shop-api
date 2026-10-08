from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Product
from orders.models import Order, OrderItem
from users.models import User

from .models import Review


class ReviewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Наушники")
        cls.product = Product.objects.create(
            category=category,
            name="Sony WH-1000XM4",
            price=Decimal("3600000"),
            stock=5,
        )
        cls.buyer = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="Sup3rSecret!42"
        )
        cls.stranger = User.objects.create_user(
            username="stranger", email="stranger@example.com", password="Sup3rSecret!42"
        )
        cls.admin = User.objects.create_superuser(
            username="boss", email="boss@example.com", password="Sup3rSecret!42"
        )

    def setUp(self):
        self.url = f"/api/products/{self.product.id}/reviews/"

    def give_purchase(self, user, status_value=Order.Status.DELIVERED):
        order = Order.objects.create(
            user=user,
            status=status_value,
            total_price=self.product.price,
            phone="+998901112233",
            address="Ташкент",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            price=self.product.price,
            quantity=1,
        )
        return order

    def test_guest_cannot_leave_review(self):
        response = self.client.post(self.url, {"rating": 5, "text": "Отлично"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_requires_purchase(self):
        self.client.force_authenticate(self.stranger)

        response = self.client.post(self.url, {"rating": 5, "text": "Отлично"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 0)

    def test_buyer_can_leave_review(self):
        self.give_purchase(self.buyer)
        self.client.force_authenticate(self.buyer)

        response = self.client.post(
            self.url, {"rating": 5, "text": "Звук отличный"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["username"], "buyer")

    def test_cancelled_order_does_not_count_as_purchase(self):
        self.give_purchase(self.buyer, status_value=Order.Status.CANCELLED)
        self.client.force_authenticate(self.buyer)

        response = self.client.post(self.url, {"rating": 4}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_one_review_per_product(self):
        self.give_purchase(self.buyer)
        self.client.force_authenticate(self.buyer)
        self.client.post(self.url, {"rating": 5}, format="json")

        response = self.client.post(self.url, {"rating": 3}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)

    def test_rating_must_be_between_one_and_five(self):
        self.give_purchase(self.buyer)
        self.client.force_authenticate(self.buyer)

        response = self.client.post(self.url, {"rating": 9}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reviews_are_public_and_shown_on_product(self):
        self.give_purchase(self.buyer)
        Review.objects.create(product=self.product, user=self.buyer, rating=4, text="Норм")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        product_response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(product_response.data["rating"], 4.0)
        self.assertEqual(product_response.data["reviews_count"], 1)

    def test_stranger_cannot_edit_someone_elses_review(self):
        review = Review.objects.create(
            product=self.product, user=self.buyer, rating=5, text="Супер"
        )
        self.client.force_authenticate(self.stranger)

        response = self.client.patch(
            f"{self.url}{review.id}/", {"rating": 1}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_review(self):
        review = Review.objects.create(
            product=self.product, user=self.buyer, rating=5, text="Супер"
        )
        self.client.force_authenticate(self.admin)

        response = self.client.delete(f"{self.url}{review.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.count(), 0)
