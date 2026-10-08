from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductBriefSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductBriefSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal", "added_at")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "items", "items_count", "total_price", "updated_at")


class CartItemCreateSerializer(serializers.ModelSerializer):
    """
    Добавление товара в корзину.

    Если товар уже лежит в корзине, количество не перезаписывается,
    а увеличивается — так ведут себя настоящие магазины.
    """

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity")

    def validate(self, attrs):
        product = attrs["product"]
        cart = self.context["cart"]
        already = CartItem.objects.filter(cart=cart, product=product).first()
        requested = attrs["quantity"] + (already.quantity if already else 0)

        if requested > product.stock:
            raise serializers.ValidationError(
                {"quantity": f"На складе осталось {product.stock} шт."}
            )
        return attrs

    def create(self, validated_data):
        cart = self.context["cart"]
        product = validated_data["product"]
        quantity = validated_data["quantity"]

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        return item


class CartItemUpdateSerializer(serializers.ModelSerializer):
    """Изменение количества уже добавленного товара."""

    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ("id", "quantity")

    def validate_quantity(self, value):
        product = self.instance.product
        if value > product.stock:
            raise serializers.ValidationError(f"На складе осталось {product.stock} шт.")
        return value
