from django.contrib import admin
from .models import Trend


@admin.register(Trend)
class TrendAdmin(admin.ModelAdmin):
    list_display = ("platform", "keyword", "score", "created_at")
    search_fields = ("platform", "keyword")
    list_filter = ("platform",)
