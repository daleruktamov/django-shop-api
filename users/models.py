from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Пользователь магазина.

    Расширяет стандартную модель Django полями профиля (телефон, адрес)
    и ролью. Роль «гость» отдельно не хранится: гость — это просто
    неавторизованный запрос.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Покупатель"
        ADMIN = "admin", "Администратор"

    email = models.EmailField("email", unique=True)
    role = models.CharField(
        "роль", max_length=16, choices=Role.choices, default=Role.CUSTOMER
    )
    phone = models.CharField("телефон", max_length=32, blank=True)
    address = models.CharField("адрес доставки", max_length=255, blank=True)
    created_at = models.DateTimeField("дата регистрации", auto_now_add=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        """Права администратора магазина."""
        return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser

    def save(self, *args, **kwargs):
        # Суперпользователь, созданный через createsuperuser, сразу получает
        # роль администратора — иначе он не смог бы править каталог через API.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)
