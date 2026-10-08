from django.db.models import Avg, Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from core.permissions import IsAdminOrReadOnly

from .filters import ProductFilter
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductWriteSerializer,
)


@extend_schema(tags=["catalog"])
class CategoryViewSet(viewsets.ModelViewSet):
    """Категории. Смотреть может любой, изменять — только администратор."""

    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ()
    search_fields = ("name", "description")
    ordering_fields = ("name", "created_at")
    ordering = ("name",)

    def get_queryset(self):
        return Category.objects.annotate(products_count=Count("products"))


@extend_schema_view(
    list=extend_schema(
        summary="Список товаров",
        description=(
            "Поиск: ?search=... по названию и описанию. "
            "Фильтры: ?category=, ?category_slug=, ?min_price=, ?max_price=, ?in_stock=. "
            "Сортировка: ?ordering=price | -price | -created_at | -sold_count | -rating."
        ),
    )
)
@extend_schema(tags=["catalog"])
class ProductViewSet(viewsets.ModelViewSet):
    """Товары. Публичный просмотр, изменение — только для администратора."""

    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ("name", "description")
    ordering_fields = ("price", "created_at", "sold_count", "rating", "name")
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = (
            Product.objects.select_related("category")
            .annotate(
                rating=Avg("reviews__rating"),
                reviews_count=Count("reviews", distinct=True),
            )
        )
        # Гости и покупатели видят только товары в продаже,
        # администратор — весь каталог, включая скрытые позиции.
        user = self.request.user
        if not (user.is_authenticated and user.is_admin):
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
