from django.urls import path
from .views import virlo_app

urlpatterns = [
    path("app/", virlo_app),
]
