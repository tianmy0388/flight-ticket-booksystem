# orders/urls.py

from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # 我的订单列表 /orders/
    path("", views.order_list, name="order_list"),

    # 创建订单：/orders/create/<flight_id>/<seat_id>/
    path(
        "create/<int:flight_id>/<int:seat_id>/",
        views.create_order,
        name="create_order",
    ),

    # 支付订单：/orders/<order_no>/pay/
    path("<str:order_no>/pay/", views.pay_order, name="pay_order"),

    # 退票：/orders/<order_no>/refund/
    path("<str:order_no>/refund/", views.refund_request, name="refund_request"),

    # 订单详情：/orders/<order_no>/
    path("<str:order_no>/", views.order_detail, name="order_detail"),
]
