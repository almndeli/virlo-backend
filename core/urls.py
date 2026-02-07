from django.urls import path
from . import views

urlpatterns = [
    path("signal/latest/", views.signal_latest),
    path("signal/history/", views.signal_history),
    path("trends/", views.trends_list),
]
