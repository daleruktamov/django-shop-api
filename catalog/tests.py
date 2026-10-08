from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Category, Product


class CatalogTestData(APITestCase):
    """Общий набор данных для тестов каталога."""

    @classmethod
    def setUpTestData(cls):
        cls.laptops = Category.objects.create(name="Ноутбуки")
        cls.phones = Category.objects.create(name="Смартфоны")

        cls.cheap_phone = Product.objects.create(
            category=cls.phones,
            name="Xiaomi Redmi Note 13",
            description="Недорогой смартфон с большой батареей",
            price=Decimal("2800000"),
            stock=10,
            sold_count=50,
        )
        cls.laptop = Product.objects.create(
            category=cls.laptops,
            name="Ноутбук Lenovo IdeaPad 3",
            description="Ноутбук для учёбы",
            price=Decimal("5400000"),
            stock=0,
            sold_count=5,
        )
        cls.hidden = Product.objects.create(
            category=cls.laptops,
            name="Снятый с продажи ноутбук",
            price=Decimal("100000"),
            stock=3,
            is_active=False,
        )

        cls.customer = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="Sup3rSecret!42"
        )
        cls.admin = User.objects.create_superuser(
            username="boss", email="boss@example.com", password="Sup3rSecret!42"
        )


class ProductListTests(CatalogTestData):
    url = "/api/products/"

    def test_guest_sees_only_active_products(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_admin_sees_hidden_products_too(self):
        self.client.force_authenticate(self.admin)

        self.assertEqual(self.client.get(self.url).data["count"], 3)

    def test_search_by_name_and_description(self):
        response = self.client.get(self.url, {"search": "учёбы"})

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.laptop.id)

    def test_filter_by_category_and_price(self):
        response = self.client.get(self.url, {"category": self.phones.id})
        self.assertEqual(response.data["count"], 1)

        response = self.client.get(self.url, {"max_price": "3000000"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.cheap_phone.id)

    def test_filter_in_stock(self):
        response = self.client.get(self.url, {"in_stock": "true"})

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.cheap_phone.id)

    def test_ordering_by_price_and_popularity(self):
        by_price = self.client.get(self.url, {"ordering": "price"}).data["results"]
        self.assertEqual(by_price[0]["id"], self.cheap_phone.id)

        by_sales = self.client.get(self.url, {"ordering": "-sold_count"}).data["results"]
        self.assertEqual(by_sales[0]["id"], self.cheap_phone.id)

    def test_pagination_is_enabled(self):
        response = self.client.get(self.url)

        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.data)


class ProductWriteAccessTests(CatalogTestData):
    url = "/api/products/"

    def payload(self):
        return {
            "category": self.phones.id,
            "name": "Samsung Galaxy A55",
            "description": "Новый смартфон",
            "price": "4200000",
            "stock": 5,
        }

    def test_guest_cannot_create_product(self):
        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_create_product(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_and_delete_product(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_id = response.data["id"]
        self.assertEqual(
            self.client.delete(f"{self.url}{created_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_slug_is_generated_automatically(self):
        product = Product.objects.create(
            category=self.phones, name="Тестовый товар", price=Decimal("1000")
        )

        self.assertTrue(product.slug)


class CategoryTests(CatalogTestData):
    url = "/api/categories/"

    def test_list_is_public_and_counts_products(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {row["name"]: row["products_count"] for row in response.data["results"]}
        self.assertEqual(names["Смартфоны"], 1)

    def test_only_admin_can_create_category(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(
            self.client.post(self.url, {"name": "Планшеты"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.post(self.url, {"name": "Планшеты"}, format="json").status_code,
            status.HTTP_201_CREATED,
        )
