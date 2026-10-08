from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("product",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "items_count", "total_price", "updated_at")
    search_fields = ("user__username", "user__email")
    inlines = [CartItemInline]
