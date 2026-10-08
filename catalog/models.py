from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Категория товаров."""

    name = models.CharField("название", max_length=120, unique=True)
    slug = models.SlugField("слаг", max_length=140, unique=True, blank=True, allow_unicode=True)
    description = models.TextField("описание", blank=True)
    created_at = models.DateTimeField("создана", auto_now_add=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Товар магазина."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="категория",
    )
    name = models.CharField("название", max_length=200)
    slug = models.SlugField("слаг", max_length=220, unique=True, blank=True, allow_unicode=True)
    description = models.TextField("описание", blank=True)
    price = models.DecimalField(
        "цена",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField("остаток на складе", default=0)
    image = models.ImageField("изображение", upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField("в продаже", default=True)
    sold_count = models.PositiveIntegerField("продано штук", default=0)
    created_at = models.DateTimeField("добавлен", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True) or "product"
            slug = base
            counter = 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.stock > 0
