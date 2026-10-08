from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


class Order(models.Model):
    """Оформленный заказ."""

    class Status(models.TextChoices):
        NEW = "new", "Новый"
        PROCESSING = "processing", "В обработке"
        SHIPPED = "shipped", "Отправлен"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменён"

    #: Из каких статусов заказ ещё можно отменить.
    CANCELLABLE = (Status.NEW, Status.PROCESSING)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="покупатель",
    )
    status = models.CharField(
        "статус", max_length=16, choices=Status.choices, default=Status.NEW
    )
    total_price = models.DecimalField(
        "сумма заказа", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    full_name = models.CharField("получатель", max_length=150, blank=True)
    phone = models.CharField("телефон", max_length=32)
    address = models.CharField("адрес доставки", max_length=255)
    comment = models.TextField("комментарий", blank=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"Заказ №{self.pk} — {self.get_status_display()}"

    @property
    def can_be_cancelled(self) -> bool:
        return self.status in self.CANCELLABLE


class OrderItem(models.Model):
    """
    Позиция заказа.

    Название и цена копируются из товара в момент оформления: если продавец
    потом поменяет цену или удалит товар, содержимое старого заказа не поедет.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="заказ"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="товар",
    )
    product_name = models.CharField("название товара", max_length=200)
    price = models.DecimalField("цена на момент покупки", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("количество", validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity
