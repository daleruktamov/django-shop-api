from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    ordering = ("-created_at",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Магазин", {"fields": ("role", "phone", "address")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Магазин", {"fields": ("email", "role", "phone", "address")}),
    )
