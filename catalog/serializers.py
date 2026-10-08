from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "products_count")
        read_only_fields = ("id", "slug", "products_count")


class CategoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class ProductListSerializer(serializers.ModelSerializer):
    """Карточка товара в списке каталога."""

    category = CategoryShortSerializer(read_only=True)
    rating = serializers.FloatField(read_only=True, default=None)
    reviews_count = serializers.IntegerField(read_only=True, default=0)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "image",
            "stock",
            "in_stock",
            "category",
            "rating",
            "reviews_count",
            "sold_count",
            "created_at",
        )


class ProductDetailSerializer(ProductListSerializer):
    """Детальная карточка — то же самое плюс описание."""

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ("description", "is_active", "updated_at")


class ProductWriteSerializer(serializers.ModelSerializer):
    """Создание и редактирование товара (только для администратора)."""

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "is_active",
        )

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля.")
        return value


class ProductBriefSerializer(serializers.ModelSerializer):
    """Минимальное представление товара — для корзины, заказов и отзывов."""

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "price", "image")
