from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
)


def get_user_cart(user) -> Cart:
    """Корзина создаётся при первом обращении, отдельный запрос не нужен."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@extend_schema(tags=["cart"])
class CartView(generics.RetrieveAPIView):
    """Содержимое корзины текущего пользователя вместе с итоговой суммой."""

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_user_cart(self.request.user)


@extend_schema(tags=["cart"])
class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Добавление товара, изменение количества и удаление позиции."""

    queryset = CartItem.objects.none()  # подсказка для генератора схемы
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Фильтр по владельцу — гарантия, что чужую корзину тронуть нельзя.
        return CartItem.objects.filter(cart__user=self.request.user).select_related("product")

    def get_serializer_class(self):
        if self.action == "create":
            return CartItemCreateSerializer
        if self.action in ("update", "partial_update"):
            return CartItemUpdateSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["cart"] = get_user_cart(self.request.user)
        return context

    @extend_schema(
        summary="Добавить товар в корзину",
        responses={201: CartSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cart = get_user_cart(request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Изменить количество", responses={200: CartSerializer})
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        cart = get_user_cart(request.user)
        return Response(CartSerializer(cart).data)


@extend_schema(tags=["cart"], responses={204: None})
class CartClearView(generics.GenericAPIView):
    """Полная очистка корзины."""

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        get_user_cart(request.user).items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
