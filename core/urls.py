from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import virlo_app, TrendViewSet, PublicTrendsViewSet

router = DefaultRouter()
router.register(r"trends", TrendViewSet, basename="trends")
router.register(r"public/trends", PublicTrendsViewSet, basename="public-trends")

urlpatterns = [
    # Frontend
    path("app/", virlo_app),

    # API
    path("", include(router.urls)),
]
