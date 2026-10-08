from rest_framework import serializers

from orders.models import Order, OrderItem

from .models import Review


class ReviewAuthorSerializer(serializers.Serializer):
    """Автор отзыва: показываем только имя, без контактов."""

    id = serializers.IntegerField()
    username = serializers.CharField()


class ReviewSerializer(serializers.ModelSerializer):
    user = ReviewAuthorSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "rating", "text", "created_at", "updated_at")
        read_only_fields = ("id", "user", "created_at", "updated_at")


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id", "rating", "text")

    def validate(self, attrs):
        product = self.context["product"]
        user = self.context["request"].user

        if Review.objects.filter(product=product, user=user).exists():
            raise serializers.ValidationError(
                {"detail": "Вы уже оставляли отзыв на этот товар."}
            )

        # Отзыв может написать только тот, кто действительно купил товар.
        has_purchase = (
            OrderItem.objects.filter(order__user=user, product=product)
            .exclude(order__status=Order.Status.CANCELLED)
            .exists()
        )
        if not has_purchase:
            raise serializers.ValidationError(
                {"detail": "Оставить отзыв можно только на купленный товар."}
            )

        return attrs

    def create(self, validated_data):
        return Review.objects.create(
            product=self.context["product"],
            user=self.context["request"].user,
            **validated_data,
        )

    def to_representation(self, instance):
        return ReviewSerializer(instance, context=self.context).data
