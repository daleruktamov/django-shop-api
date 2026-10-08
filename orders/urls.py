from rest_framework.routers import DefaultRouter

from .views import OrderViewSet

router = DefaultRouter()
router.register("", OrderViewSet, basename="order")

app_name = "orders"

urlpatterns = router.urls
