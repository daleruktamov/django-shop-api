"""
Наполнение базы демонстрационными данными.

Команда идемпотентна: её можно запускать повторно, дубликатов не появится.

    python manage.py seed_demo
"""

import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product

User = get_user_model()

CATEGORIES = [
    ("Ноутбуки", "Портативные компьютеры для работы и учёбы"),
    ("Смартфоны", "Мобильные телефоны и аксессуары к ним"),
    ("Наушники", "Проводные и беспроводные наушники"),
    ("Клавиатуры", "Механические и мембранные клавиатуры"),
]

PRODUCTS = [
    ("Ноутбуки", "Ноутбук Lenovo IdeaPad 3", "15.6 дюйма, Ryzen 5, 16 ГБ ОЗУ, SSD 512 ГБ", "5400000", 7),
    ("Ноутбуки", "Ноутбук ASUS VivoBook 15", "Intel Core i5, 8 ГБ ОЗУ, SSD 512 ГБ", "6100000", 4),
    ("Ноутбуки", "MacBook Air 13 M2", "Apple M2, 8 ГБ памяти, SSD 256 ГБ", "13500000", 2),
    ("Смартфоны", "Samsung Galaxy A55", "6.6 дюйма AMOLED, 128 ГБ, две SIM-карты", "4200000", 12),
    ("Смартфоны", "Xiaomi Redmi Note 13", "Экран 120 Гц, батарея 5000 мА·ч", "2800000", 20),
    ("Смартфоны", "iPhone 15", "128 ГБ, разъём USB-C, камера 48 Мп", "11900000", 5),
    ("Наушники", "Sony WH-1000XM4", "Полноразмерные, с активным шумоподавлением", "3600000", 6),
    ("Наушники", "Apple AirPods Pro 2", "Внутриканальные, с шумоподавлением и USB-C", "3100000", 9),
    ("Наушники", "JBL Tune 510BT", "Беспроводные, до 40 часов работы", "620000", 25),
    ("Клавиатуры", "Keychron K2 Pro", "Механическая, 75%, горячая замена свитчей", "1450000", 8),
    ("Клавиатуры", "Logitech K380", "Компактная, до трёх устройств по Bluetooth", "480000", 15),
    ("Клавиатуры", "Razer BlackWidow V4", "Механическая, свитчи Green, подсветка RGB", "2200000", 3),
]


class Command(BaseCommand):
    help = "Заполняет базу демонстрационными категориями, товарами и пользователями"

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-password",
            default=os.getenv("ADMIN_PASSWORD", "admin12345"),
            help="Пароль для демонстрационного администратора",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for name, description in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            categories[name] = category
            if created:
                self.stdout.write(f"  + категория: {name}")

        for category_name, name, description, price, stock in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": categories[category_name],
                    "description": description,
                    "price": Decimal(price),
                    "stock": stock,
                },
            )
            if created:
                self.stdout.write(f"  + товар: {name}")

        password = options["admin_password"]

        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@shop.local",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password(password)
            admin.save()
            self.stdout.write(f"  + администратор: admin / {password}")

        customer, created = User.objects.get_or_create(
            username="customer",
            defaults={
                "email": "customer@shop.local",
                "first_name": "Иван",
                "last_name": "Покупателев",
                "phone": "+998901234567",
                "address": "г. Ташкент, ул. Амира Темура, 1",
            },
        )
        if created:
            customer.set_password("customer12345")
            customer.save()
            self.stdout.write("  + покупатель: customer / customer12345")

        self.stdout.write(self.style.SUCCESS("Демонстрационные данные готовы."))
