from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CartClearView, CartItemViewSet, CartView

router = DefaultRouter()
router.register("items", CartItemViewSet, basename="cart-item")

app_name = "cart"

urlpatterns = [
    path("", CartView.as_view(), name="cart-detail"),
    path("clear/", CartClearView.as_view(), name="cart-clear"),
    path("", include(router.urls)),
]
