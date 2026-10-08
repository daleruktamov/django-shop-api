from decimal import Decimal

from django.db import connection, transaction
from rest_framework import serializers

from cart.models import Cart
from catalog.models import Product
from catalog.serializers import ProductBriefSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductBriefSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "price", "quantity", "subtotal")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "status_display",
            "total_price",
            "full_name",
            "phone",
            "address",
            "comment",
            "items",
            "can_be_cancelled",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Оформление заказа из корзины.

    Данные доставки можно не передавать: тогда берутся телефон и адрес
    из профиля пользователя.
    """

    class Meta:
        model = Order
        fields = ("id", "full_name", "phone", "address", "comment")
        extra_kwargs = {
            "phone": {"required": False, "allow_blank": True},
            "address": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        user = self.context["request"].user

        attrs["phone"] = (attrs.get("phone") or user.phone).strip()
        attrs["address"] = (attrs.get("address") or user.address).strip()
        attrs["full_name"] = (
            attrs.get("full_name") or user.get_full_name() or user.username
        ).strip()

        errors = {}
        if not attrs["phone"]:
            errors["phone"] = "Укажите телефон: в профиле он не заполнен."
        if not attrs["address"]:
            errors["address"] = "Укажите адрес доставки: в профиле он не заполнен."
        if errors:
            raise serializers.ValidationError(errors)

        cart = Cart.objects.filter(user=user).first()
        cart_items = list(cart.items.select_related("product")) if cart else []
        if not cart_items:
            raise serializers.ValidationError({"detail": "Корзина пуста."})

        attrs["_cart"] = cart
        attrs["_cart_items"] = cart_items
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        cart = validated_data.pop("_cart")
        cart_items = validated_data.pop("_cart_items")
        user = self.context["request"].user

        # Блокируем строки товаров, чтобы два одновременных заказа не увели
        # склад в минус. На SQLite блокировок нет, там просто читаем.
        products_qs = Product.objects.filter(
            pk__in=[item.product_id for item in cart_items]
        )
        if connection.features.has_select_for_update:
            products_qs = products_qs.select_for_update()
        products = {product.pk: product for product in products_qs}

        order_items = []
        total = Decimal("0.00")

        for item in cart_items:
            product = products.get(item.product_id)
            if product is None or not product.is_active:
                raise serializers.ValidationError(
                    {"detail": f"Товар {item.product.name} больше не продаётся."}
                )
            if product.stock < item.quantity:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            f"Товара {product.name} осталось {product.stock} шт., "
                            f"а в корзине {item.quantity}."
                        )
                    }
                )

            order_items.append(
                OrderItem(
                    product=product,
                    product_name=product.name,
                    price=product.price,
                    quantity=item.quantity,
                )
            )
            total += product.price * item.quantity

            product.stock -= item.quantity
            product.sold_count += item.quantity
            product.save(update_fields=["stock", "sold_count"])

        order = Order.objects.create(user=user, total_price=total, **validated_data)
        for order_item in order_items:
            order_item.order = order
        OrderItem.objects.bulk_create(order_items)

        cart.items.all().delete()
        return order

    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data


class OrderStatusSerializer(serializers.ModelSerializer):
    """Смена статуса заказа, доступна только администратору."""

    class Meta:
        model = Order
        fields = ("id", "status")
