from django.db.models import Max
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .models import Trend
from .serializers import TrendSerializer


# -------------------------
# Pagination (Unified response)
# -------------------------
class UnifiedLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "meta": {
                    "count": self.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "limit": self.limit,
                    "offset": self.offset,
                },
                "results": data,
            }
        )


class PublicUnifiedPagination(UnifiedLimitOffsetPagination):
    default_limit = 5
    max_limit = 5  # public stays small


# -------------------------
# Helpers
# -------------------------
ALLOWED_ORDERING = {"created_at", "-created_at", "score", "-score", "id", "-id"}


def apply_filters_and_ordering(request, qs):
    # Filters
    platform = request.query_params.get("platform")
    keyword = request.query_params.get("keyword")
    q = request.query_params.get("q")  # quick search

    if platform:
        qs = qs.filter(platform__iexact=platform.strip())

    if keyword:
        qs = qs.filter(keyword__iexact=keyword.strip())

    if q:
        q = q.strip()
        qs = qs.filter(keyword__icontains=q) | qs.filter(platform__icontains=q)

    # Ordering
    ordering = request.query_params.get("ordering", "-created_at").strip()
    if ordering not in ALLOWED_ORDERING:
        ordering = "-created_at"

    return qs.order_by(ordering)


# -------------------------
# ViewSets
# -------------------------
class TrendViewSet(viewsets.ModelViewSet):
    serializer_class = TrendSerializer

    def get_permissions(self):
        # Public read-only for demo
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]
    permission_classes = [IsAuthenticated]
    pagination_class = UnifiedLimitOffsetPagination

    def get_queryset(self):
        # latest record per (platform, keyword)
        latest_ids = (
            Trend.objects.values("platform", "keyword")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )

        qs = Trend.objects.filter(id__in=list(latest_ids))
        qs = apply_filters_and_ordering(self.request, qs)
        return qs


class PublicTrendsViewSet(TrendViewSet):
    permission_classes = [AllowAny]
    http_method_names = ["get"]  # public read-only
    pagination_class = PublicUnifiedPagination

    def get_queryset(self):
        # same logic as TrendViewSet but stays small via pagination max_limit=5
        return super().get_queryset()


def virlo_app(request):
    return render(request, "virlo/app.html")
