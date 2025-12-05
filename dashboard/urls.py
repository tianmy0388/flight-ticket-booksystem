# dashboard/urls.py

from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.admin_login, name="admin_login"),
    path("revenue/", views.revenue_overview, name="revenue_overview"),

    # 航班管理
    path("flights/", views.flight_list, name="flight_list"),
    path("flights/add/", views.flight_create, name="flight_create"),
    path("flights/<int:pk>/edit/", views.flight_update, name="flight_update"),
    path("flights/<int:pk>/delete/", views.flight_delete, name="flight_delete"),
]
