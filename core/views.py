from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request: Request) -> Response:
    """Короткая справка по корневому адресу — куда идти дальше."""
    return Response(
        {
            "name": "Shop API",
            "version": "1.0.0",
            "docs": request.build_absolute_uri(reverse("swagger-ui")),
            "redoc": request.build_absolute_uri(reverse("redoc")),
            "schema": request.build_absolute_uri(reverse("schema")),
            "endpoints": {
                "register": request.build_absolute_uri("/api/auth/register/"),
                "login": request.build_absolute_uri("/api/auth/login/"),
                "products": request.build_absolute_uri("/api/products/"),
                "categories": request.build_absolute_uri("/api/categories/"),
                "cart": request.build_absolute_uri("/api/cart/"),
                "orders": request.build_absolute_uri("/api/orders/"),
            },
        }
    )
