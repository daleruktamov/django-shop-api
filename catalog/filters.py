import django_filters as filters

from .models import Product


class ProductFilter(filters.FilterSet):
    """Фильтрация каталога по категории, цене и наличию."""

    category = filters.NumberFilter(field_name="category_id", label="ID категории")
    category_slug = filters.CharFilter(
        field_name="category__slug", lookup_expr="iexact", label="Слаг категории"
    )
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte", label="Цена от")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte", label="Цена до")
    in_stock = filters.BooleanFilter(method="filter_in_stock", label="Только в наличии")

    class Meta:
        model = Product
        fields = ("category", "category_slug", "min_price", "max_price", "in_stock")

    def filter_in_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(stock__gt=0)
        if value is False:
            return queryset.filter(stock=0)
        return queryset
