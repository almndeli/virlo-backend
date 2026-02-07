from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# removed virlo.api import for render deploy

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API (direct)
    # removed velocity_est route for render deploy

    # API (core)
    path("api/", include("core.urls")),

    # Frontend
    path("app/", include("core.front_urls")),
]




