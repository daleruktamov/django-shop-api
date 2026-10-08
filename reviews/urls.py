from django.urls import path

from .views import ReviewDetailView, ReviewListCreateView

app_name = "reviews"

urlpatterns = [
    path(
        "products/<int:product_id>/reviews/",
        ReviewListCreateView.as_view(),
        name="review-list",
    ),
    path(
        "products/<int:product_id>/reviews/<int:pk>/",
        ReviewDetailView.as_view(),
        name="review-detail",
    ),
]
