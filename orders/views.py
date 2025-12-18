# from django.shortcuts import render
#
# # Create your views here.
import uuid
from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import Http404, HttpResponseNotAllowed
from django.db.models import Q

from flights.models import Flight, FlightSeat
from accounts.models import PassengerProfile
from .models import TicketOrder, OrderStatus, RefundRecord, RefundStatus
from .forms import RefundRequestForm


def _generate_order_no():
    return uuid.uuid4().hex[:20]


def _calc_tax(price: Decimal) -> Decimal:
    return (price * Decimal("0.05")).quantize(Decimal("0.01"))


def _calc_refund_fee(order: TicketOrder):
    now = timezone.now()
    flight = order.flight
    delta = flight.depart_time - now
    hours = delta.total_seconds() / 3600

    price = order.ticket_price
    if hours > 48:
        rate = Decimal("0.05")
    elif hours > 24:
        rate = Decimal("0.10")
    elif hours > 0:
        rate = Decimal("0.20")
    else:
        # 起飞后不允许退票
        raise ValueError("航班已起飞，无法退票")

    fee = (price * rate).quantize(Decimal("0.01"))
    refund_amount = (order.total_amount - fee).quantize(Decimal("0.01"))
    return fee, refund_amount


def _refresh_order_status(order: TicketOrder) -> TicketOrder:
    """
    自动处理未支付订单的过期状态，并补充支付截止时间/倒计时信息。
    """
    if order.status == OrderStatus.RESERVED:
        deadline = order.created_at + timedelta(minutes=15)
        now = timezone.now()
        if now >= deadline:
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = now
            order.save(update_fields=["status", "cancelled_at"])
            # 归还座位
            seat = order.seat
            seat.available_seats += 1
            seat.save(update_fields=["available_seats"])
        else:
            order.payment_deadline = deadline
            order.remaining_seconds = int((deadline - now).total_seconds())
    return order


@login_required
def create_order(request, flight_id, seat_id):
    flight = get_object_or_404(Flight, pk=flight_id)
    seat = get_object_or_404(FlightSeat, pk=seat_id, flight=flight)

    # 管理员账号不参与购票，给出友好提示
    if request.user.is_staff:
        return render(
            request,
            "orders/order_error.html",
            {"message": "管理员账号仅用于后台管理，不支持在线购票。请使用乘客账号下单。"},
        )

    profile: PassengerProfile = request.user.profile

    if flight.status != "ON_SALE":
        raise Http404("航班不可售")

    # 同一用户同一航班不得重复预订/支付（仅排除已取消或已退票的订单）
    existing = TicketOrder.objects.filter(
        user=request.user,
        flight=flight,
    ).exclude(status__in=[OrderStatus.CANCELLED, OrderStatus.REFUNDED])
    if existing.exists():
        return render(
            request,
            "orders/order_error.html",
            {"message": "您已对该航班有预订或已支付订单，请勿重复下单。可在“我的订单”查看进度。"},
        )

    if request.method == "POST":
        with transaction.atomic():
            seat_for_update = (
                FlightSeat.objects.select_for_update()
                .select_related("flight")
                .get(pk=seat_id)
            )
            if seat_for_update.available_seats <= 0:
                return render(
                    request,
                    "orders/order_error.html",
                    {"message": "该舱位余票不足，请选择其他航班或舱位"},
                )

            seat_for_update.available_seats -= 1
            seat_for_update.save()

            ticket_price = seat_for_update.price
            tax = _calc_tax(ticket_price)
            total_amount = ticket_price + tax

            order = TicketOrder.objects.create(
                order_no=_generate_order_no(),
                user=request.user,
                profile=profile,
                flight=flight,
                seat=seat_for_update,
                status=OrderStatus.RESERVED,
                ticket_price=ticket_price,
                tax=tax,
                total_amount=total_amount,
            )

        return redirect("orders:order_detail", order_no=order.order_no)

    # 简单确认页
    return render(
        request,
        "orders/order_confirm.html",
        {"flight": flight, "seat": seat, "profile": profile},
    )


@login_required
def order_list(request):
    orders_qs = (
        TicketOrder.objects.filter(user=request.user)
        .select_related("flight", "seat")
        .order_by("-created_at")
    )
    orders = [_refresh_order_status(o) for o in orders_qs]
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail(request, order_no):
    order = get_object_or_404(
        TicketOrder.objects.select_related("flight", "seat", "profile"),
        order_no=order_no,
        user=request.user,
    )
    order = _refresh_order_status(order)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def refund_request(request, order_no):
    order = get_object_or_404(
        TicketOrder.objects.select_related("flight", "seat"),
        order_no=order_no,
        user=request.user,
    )
    if order.status != OrderStatus.PAID:
        return render(
            request,
            "orders/order_error.html",
            {"message": "只有已支付订单可以申请退票"},
        )

    try:
        fee, refund_amount = _calc_refund_fee(order)
    except ValueError as e:
        return render(request, "orders/order_error.html", {"message": str(e)})

    if request.method == "POST":
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data["reason"]
            with transaction.atomic():
                RefundRecord.objects.create(
                    order=order,
                    status=RefundStatus.APPROVED,
                    refund_amount=refund_amount,
                    refund_fee=fee,
                    reason=reason,
                    approve_time=timezone.now(),
                )

                order.status = OrderStatus.REFUNDED
                order.fee = fee
                order.refunded_at = timezone.now()
                order.save()

                seat_for_update = (
                    FlightSeat.objects.select_for_update().get(pk=order.seat_id)
                )
                seat_for_update.available_seats += 1
                seat_for_update.save()

            return redirect("orders:order_detail", order_no=order.order_no)
    else:
        form = RefundRequestForm()

    return render(
        request,
        "orders/refund_confirm.html",
        {
            "order": order,
            "fee": fee,
            "refund_amount": refund_amount,
            "form": form,
        },
    )


@login_required
def pay_order(request, order_no):
    order = get_object_or_404(
        TicketOrder.objects.select_related("flight", "seat"),
        order_no=order_no,
        user=request.user,
    )
    order = _refresh_order_status(order)
    if order.status == OrderStatus.CANCELLED:
        return render(
            request,
            "orders/order_error.html",
            {"message": "超过支付时限，订单已取消"},
        )
    if order.status != OrderStatus.RESERVED:
        return redirect("orders:order_detail", order_no=order.order_no)

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    order.status = OrderStatus.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at"])
    return redirect("orders:order_detail", order_no=order.order_no)
