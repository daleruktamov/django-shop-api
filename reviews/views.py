from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions

from catalog.models import Product
from core.permissions import IsAuthorOrReadOnly

from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer


class ProductScopedMixin:
    """Все отзывы живут внутри конкретного товара: /api/products/{id}/reviews/."""

    queryset = Review.objects.none()  # подсказка для генератора схемы

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs["product_id"])

    def get_queryset(self):
        return (
            Review.objects.filter(product_id=self.kwargs["product_id"])
            .select_related("user")
        )


@extend_schema_view(
    get=extend_schema(summary="Отзывы о товаре", responses={200: ReviewSerializer}),
    post=extend_schema(
        summary="Оставить отзыв",
        description="Доступно только покупателю, у которого есть заказ с этим товаром.",
        responses={201: ReviewSerializer},
    ),
)
@extend_schema(tags=["reviews"])
class ReviewListCreateView(ProductScopedMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    ordering_fields = ("created_at", "rating")
    ordering = ("-created_at",)

    def get_serializer_class(self):
        return ReviewCreateSerializer if self.request.method == "POST" else ReviewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.get_product()
        return context


@extend_schema(tags=["reviews"])
class ReviewDetailView(ProductScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """Редактировать и удалять отзыв может его автор или администратор."""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
