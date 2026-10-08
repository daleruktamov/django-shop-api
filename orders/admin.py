from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    list_editable = ("status",)
    search_fields = ("id", "user__username", "user__email", "phone", "address")
    readonly_fields = ("user", "total_price", "created_at", "updated_at")
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
