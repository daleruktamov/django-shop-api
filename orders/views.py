from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, viewsets
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsOwnerOrAdmin

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer, OrderStatusSerializer


@extend_schema(tags=["orders"])
class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Заказы.

    Покупатель видит только свои заказы, администратор видит все.
    """

    # Пустой queryset нужен только генератору схемы, чтобы он понял модель.
    # Реальная выборка всегда собирается в get_queryset().
    queryset = Order.objects.none()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filterset_fields = ("status",)
    ordering_fields = ("created_at", "total_price")
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = Order.objects.prefetch_related("items__product").select_related("user")
        user = self.request.user
        if not (user.is_authenticated and user.is_admin):
            queryset = queryset.filter(user=user)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "set_status":
            return OrderStatusSerializer
        return OrderSerializer

    @extend_schema(
        summary="Оформить заказ из корзины",
        description=(
            "Переносит содержимое корзины в заказ: фиксирует цены, списывает "
            "остатки со склада и очищает корзину."
        ),
        responses={201: OrderSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Сменить статус заказа (администратор)",
        responses={200: OrderSerializer},
    )
    @action(
        detail=True,
        methods=["patch"],
        url_path="status",
        permission_classes=[permissions.IsAdminUser],
    )
    def set_status(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    @extend_schema(
        summary="Отменить заказ",
        description=(
            "Отменить можно заказ в статусе «новый» или «в обработке». "
            "Товары возвращаются на склад."
        ),
        request=None,
        responses={200: OrderSerializer},
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()

        if not order.can_be_cancelled:
            return Response(
                {
                    "detail": (
                        f"Заказ в статусе «{order.get_status_display()}» "
                        f"отменить нельзя."
                    )
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in order.items.select_related("product"):
                if item.product is not None:
                    item.product.stock += item.quantity
                    item.product.sold_count = max(
                        0, item.product.sold_count - item.quantity
                    )
                    item.product.save(update_fields=["stock", "sold_count"])

            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status", "updated_at"])

        return Response(OrderSerializer(order).data)
