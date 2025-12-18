# dashboard/views.py

from decimal import Decimal
from datetime import date, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
        # django.contrib 导入
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from orders.models import TicketOrder, OrderStatus
from flights.models import Flight, FlightSeat, CabinClass, FlightStatus
from flights.forms import FlightAdminForm


# --------------------- 舱位价格倍数 ---------------------

CABIN_MULTIPLIERS = {
    CabinClass.ECONOMY: Decimal("1.0"),
    CabinClass.BUSINESS: Decimal("1.5"),
    CabinClass.FIRST: Decimal("2.0"),
}


def _sync_cabin_seat(flight, cabin_class, new_available: int):
    """
    同步某个舱位的“剩余座位数”和价格。

    约定：
    - new_available >= 0
    - total_seats 始终保持 = 已售出票数 + 剩余座位数
    """
    if new_available is None:
        new_available = 0
    if new_available < 0:
        new_available = 0

    qs = FlightSeat.objects.filter(flight=flight, cabin_class=cabin_class)
    multiplier = CABIN_MULTIPLIERS[cabin_class]
    price = (flight.base_price * multiplier).quantize(Decimal("0.01"))

    if not qs.exists():
        # 之前没有这个舱位记录
        if new_available == 0:
            # 仍然没有座位，直接不创建即可
            return
        FlightSeat.objects.create(
            flight=flight,
            cabin_class=cabin_class,
            total_seats=new_available,
            available_seats=new_available,
            price=price,
        )
        return

    # 已经存在该舱位记录
    seat = qs.get()
    sold = TicketOrder.objects.filter(
        flight=flight, seat=seat, status=OrderStatus.PAID
    ).count()

    seat.total_seats = sold + new_available
    seat.available_seats = new_available
    seat.price = price
    seat.save()


# --------------------- 管理员登录 ---------------------


def admin_login(request):
    """
    管理员单独登录入口：
    - 使用普通 User 账号
    - 但只允许 is_staff=True 的登录成功
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard:revenue_overview")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                form.add_error(None, "该账号不是管理员账号")
            else:
                login(request, user)
                return redirect("dashboard:revenue_overview")
    else:
        form = AuthenticationForm(request)
    return render(request, "dashboard/admin_login.html", {"form": form})


# --------------------- 营收统计（年 / 月 / 周） ---------------------


@staff_member_required
def revenue_overview(request):
    """
    营收统计页面：
    - 顶部：按年统计（可选年份）
    - 中间：按月统计（可选年月）
    - 底部：按周统计（可选周起始日期）

    默认：
    - 年：当前年份
    - 月：当前年月
    - 周：当前周（周一为起始）
    """
    today = timezone.localdate()

    # 年份选择
    try:
        selected_year = int(request.GET.get("year") or today.year)
    except ValueError:
        selected_year = today.year

    # 月份选择（格式 YYYY-MM）
    month_param = request.GET.get("month")
    if month_param:
        try:
            y, m = [int(p) for p in month_param.split("-")]
            selected_month = f"{y:04d}-{m:02d}"
            month_year, month_month = y, m
        except Exception:
            month_year, month_month = today.year, today.month
            selected_month = f"{month_year:04d}-{month_month:02d}"
    else:
        month_year, month_month = today.year, today.month
        selected_month = f"{month_year:04d}-{month_month:02d}"

    # 周起始日期选择（日期控件）
    week_param = request.GET.get("week_start")
    if week_param:
        try:
            week_start = date.fromisoformat(week_param)
        except ValueError:
            week_start = today - timedelta(days=today.weekday())
    else:
        # 当前周的周一
        week_start = today - timedelta(days=today.weekday())
    selected_week_start = week_start.isoformat()
    week_end = week_start + timedelta(days=7)

    paid_orders = TicketOrder.objects.filter(status=OrderStatus.PAID)
    refunded_orders = TicketOrder.objects.filter(status=OrderStatus.REFUNDED)

    def _sum_paid(**kwargs):
        return (
            paid_orders.filter(**kwargs)
            .aggregate(total=Sum("total_amount"))
            .get("total")
            or Decimal("0.00")
        )

    def _sum_refund_fee(**kwargs):
        return (
            refunded_orders.filter(**kwargs)
            .aggregate(total=Sum("fee"))
            .get("total")
            or Decimal("0.00")
        )

    # 按年合计
    yearly_total = _sum_paid(paid_at__year=selected_year) + _sum_refund_fee(
        refunded_at__year=selected_year
    )

    # 按月合计
    monthly_total = _sum_paid(
        paid_at__year=month_year, paid_at__month=month_month
    ) + _sum_refund_fee(refunded_at__year=month_year, refunded_at__month=month_month)

    # 按周合计（[week_start, week_end)）
    weekly_total = _sum_paid(
        paid_at__date__gte=week_start, paid_at__date__lt=week_end
    ) + _sum_refund_fee(
        refunded_at__date__gte=week_start, refunded_at__date__lt=week_end
    )

    # 月度营收分布（用于柱状图）
    monthly_chart_labels = [f"{m}月" for m in range(1, 13)]
    monthly_chart_data = []
    for m in range(1, 13):
        month_total = _sum_paid(paid_at__year=selected_year, paid_at__month=m) + _sum_refund_fee(
            refunded_at__year=selected_year, refunded_at__month=m
        )
        monthly_chart_data.append(float(month_total))

    # 本周每天营收（用于补充趋势展示）
    weekly_chart_labels = []
    weekly_chart_data = []
    for i in range(7):
        current_day = week_start + timedelta(days=i)
        weekly_chart_labels.append(current_day.strftime("%m-%d"))
        daily_total = _sum_paid(paid_at__date=current_day) + _sum_refund_fee(
            refunded_at__date=current_day
        )
        weekly_chart_data.append(float(daily_total))

    return render(
        request,
        "dashboard/revenue_overview.html",
        {
            "selected_year": selected_year,
            "selected_month": selected_month,
            "selected_week_start": selected_week_start,
            "week_end": week_end,
            "yearly_total": yearly_total,
            "monthly_total": monthly_total,
            "weekly_total": weekly_total,
            "monthly_chart_labels": monthly_chart_labels,
            "monthly_chart_data": monthly_chart_data,
            "weekly_chart_labels": weekly_chart_labels,
            "weekly_chart_data": weekly_chart_data,
        },
    )


# --------------------- 航班管理 ---------------------


@staff_member_required
def flight_list(request):
    """
    航班列表：管理员在这里查看 / 管理所有航班
    """
    now = timezone.now()
    cutoff = now + timedelta(hours=1)
    Flight.objects.filter(status=FlightStatus.ON_SALE, depart_time__lte=cutoff).update(
        status=FlightStatus.FINISHED
    )

    flights = (
        Flight.objects.select_related("depart_airport", "arrive_airport")
        .order_by("depart_time")
    )
    return render(request, "dashboard/flight_list.html", {"flights": flights})


@staff_member_required
def flight_create(request):
    """
    新增航班：
    - 保存 Flight
    - 根据表单中的各舱“剩余座位数”，创建对应的 FlightSeat
    """
    if request.method == "POST":
        form = FlightAdminForm(request.POST)
        if form.is_valid():
            flight = form.save()

            econ = form.cleaned_data.get("economy_seats") or 0
            biz = form.cleaned_data.get("business_seats") or 0
            fst = form.cleaned_data.get("first_seats") or 0

            _sync_cabin_seat(flight, CabinClass.ECONOMY, econ)
            _sync_cabin_seat(flight, CabinClass.BUSINESS, biz)
            _sync_cabin_seat(flight, CabinClass.FIRST, fst)

            messages.success(request, "航班创建成功")
            return redirect("dashboard:flight_list")
    else:
        form = FlightAdminForm()
    return render(
        request,
        "dashboard/flight_form.html",
        {"form": form, "is_create": True},
    )


@staff_member_required
def flight_update(request, pk):
    """
    编辑航班：
    - 更新 Flight
    - 同步更新各舱位 FlightSeat 的“剩余座位数”和价格
    """
    flight = get_object_or_404(Flight, pk=pk)

    if request.method == "POST":
        form = FlightAdminForm(request.POST, instance=flight)
        if form.is_valid():
            flight = form.save()

            econ = form.cleaned_data.get("economy_seats") or 0
            biz = form.cleaned_data.get("business_seats") or 0
            fst = form.cleaned_data.get("first_seats") or 0

            _sync_cabin_seat(flight, CabinClass.ECONOMY, econ)
            _sync_cabin_seat(flight, CabinClass.BUSINESS, biz)
            _sync_cabin_seat(flight, CabinClass.FIRST, fst)

            messages.success(request, "航班信息已更新")
            return redirect("dashboard:flight_list")
    else:
        form = FlightAdminForm(instance=flight)
    return render(
        request,
        "dashboard/flight_form.html",
        {"form": form, "is_create": False, "flight": flight},
    )


@staff_member_required
def flight_delete(request, pk):
    """
    删除航班：
    - 如果该航班已经产生订单，由于 TicketOrder.flight on_delete=PROTECT，会抛 ProtectedError
    """
    flight = get_object_or_404(Flight, pk=pk)

    if request.method == "POST":
        try:
            flight.delete()
            messages.success(request, "航班已删除")
        except ProtectedError:
            messages.error(request, "该航班已存在订单，无法删除")
        return redirect("dashboard:flight_list")

    return render(request, "dashboard/flight_confirm_delete.html", {"flight": flight})
