from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "products_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="товаров")
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "sold_count")
    list_filter = ("category", "is_active")
    list_editable = ("price", "stock", "is_active")
    search_fields = ("name", "description")
    autocomplete_fields = ("category",)
    readonly_fields = ("sold_count", "created_at", "updated_at")
