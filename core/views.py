from django.db.models import Max
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import api_view, permission_classes

from .models import Trend
from .serializers import TrendSerializer


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
    max_limit = 5


ALLOWED_ORDERING = {"created_at", "-created_at", "score", "-score", "id", "-id"}


def apply_filters_and_ordering(request, qs):
    platform = request.query_params.get("platform")
    keyword = request.query_params.get("keyword")
    q = request.query_params.get("q")

    if platform:
        qs = qs.filter(platform__iexact=platform.strip())

    if keyword:
        qs = qs.filter(keyword__iexact=keyword.strip())

    if q:
        q = q.strip()
        qs = qs.filter(keyword__icontains=q) | qs.filter(platform__icontains=q)

    ordering = request.query_params.get("ordering", "-created_at").strip()
    if ordering not in ALLOWED_ORDERING:
        ordering = "-created_at"

    return qs.order_by(ordering)


class TrendViewSet(viewsets.ModelViewSet):
    serializer_class = TrendSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    permission_classes = [IsAuthenticated]
    pagination_class = UnifiedLimitOffsetPagination

    def get_queryset(self):
        latest_ids = (
            Trend.objects.values("platform", "keyword")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )
        qs = Trend.objects.filter(id__in=list(latest_ids))
        return apply_filters_and_ordering(self.request, qs)


class PublicTrendsViewSet(TrendViewSet):
    permission_classes = [AllowAny]
    http_method_names = ["get"]
    pagination_class = PublicUnifiedPagination


def virlo_app(request):
    return render(request, "virlo/app.html")


def compute_decision(score):
    if score >= 70:
        return "BUY"
    elif score >= 50:
        return "WATCH"
    return "DROP"


@api_view(["GET"])
@permission_classes([AllowAny])
def signal_latest(request):
    t = Trend.objects.order_by("-created_at").first()
    if not t:
        return Response({"status": "NoData", "score": None, "decision": None})

    score = float(t.score)
    decision = compute_decision(score)
    status = "Growing" if score >= 50 else "Flat"

    return Response(
        {
            "status": status,
            "score": score,
            "decision": decision,
            "platform": t.platform,
            "keyword": t.keyword,
            "created_at": t.created_at,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def signal_history(request):
    limit = int(request.GET.get("limit", 10))

    platform = request.GET.get("platform")
    keyword = request.GET.get("keyword")
    q = request.GET.get("q")

    qs = Trend.objects.all()

    if platform:
        qs = qs.filter(platform__iexact=platform.strip())
    if keyword:
        qs = qs.filter(keyword__iexact=keyword.strip())
    if q:
        q = q.strip()
        qs = qs.filter(keyword__icontains=q) | qs.filter(platform__icontains=q)

    trends = qs.order_by("-created_at")[:limit]

    return Response(
        [
            {
                "date": t.created_at,
                "score": t.score,
                "decision": compute_decision(float(t.score)),
                "velocity_label": "Growing",
            }
            for t in trends
        ]
    )

@api_view(["GET"])
@permission_classes([AllowAny])
def trends_list(request):
    """
    Public endpoint: GET /api/trends/?limit=&offset=&platform=&keyword=&q=&ordering=
    Returns: { meta: {...}, results: [...] }
    """
    qs = Trend.objects.all()
    qs = apply_filters_and_ordering(request, qs)

    paginator = UnifiedLimitOffsetPagination()
    page = paginator.paginate_queryset(qs, request)

    serializer = TrendSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)

