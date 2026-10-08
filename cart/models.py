from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


class Cart(models.Model):
    """Корзина пользователя. У каждого покупателя она одна."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="пользователь",
    )
    created_at = models.DateTimeField("создана", auto_now_add=True)
    updated_at = models.DateTimeField("изменена", auto_now=True)

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "корзины"

    def __str__(self):
        return f"Корзина {self.user.username}"

    @property
    def total_price(self) -> Decimal:
        """Сумма корзины считается на лету по актуальным ценам товаров."""
        return sum((item.subtotal for item in self.items.all()), Decimal("0.00"))

    @property
    def items_count(self) -> int:
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Позиция корзины: товар и его количество."""

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items", verbose_name="корзина"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="товар",
    )
    quantity = models.PositiveIntegerField(
        "количество", default=1, validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField("добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "позиция корзины"
        verbose_name_plural = "позиции корзины"
        ordering = ["added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_product_per_cart"
            )
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return self.product.price * self.quantity
