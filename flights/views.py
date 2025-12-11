# flights/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Min, Q

from .models import Flight, FlightSeat, FlightStatus
from .forms import FlightSearchForm


def home(request):
    return render(request, "welcome.html")


def flight_search(request):
    form = FlightSearchForm(request.GET or None)
    flights = []
    searched = False

    if form.is_valid():
        searched = True
        depart_city = form.cleaned_data.get("depart_city", "").strip()
        arrive_city = form.cleaned_data["arrive_city"].strip()
        depart_date = form.cleaned_data["depart_date"]
        sort = form.cleaned_data.get("sort") or "price"

        # ① 构建“目的城市”搜索条件（必定有值）
        dest_q = (
            Q(arrive_airport__city__icontains=arrive_city)
            | Q(arrive_airport__name__icontains=arrive_city)
            | Q(arrive_airport__code__icontains=arrive_city)
        )

        # ② 如果填了出发地城市，再叠加一个“出发城市”条件
        filters = dest_q
        if depart_city:
            origin_q = (
                Q(depart_airport__city__icontains=depart_city)
                | Q(depart_airport__name__icontains=depart_city)
                | Q(depart_airport__code__icontains=depart_city)
            )
            filters &= origin_q

        qs = (
            Flight.objects.filter(
                filters,
                depart_time__date=depart_date,
                status=FlightStatus.ON_SALE,
                seats__available_seats__gt=0,
            )
            .annotate(min_price=Min("seats__price"))
            .distinct()
        )

        if sort == "depart_time":
            qs = qs.order_by("depart_time")
        else:
            qs = qs.order_by("min_price")

        flights = qs

    return render(
        request,
        "flights/search_results.html",
        {"form": form, "flights": flights, "searched": searched},
    )


def flight_detail(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    seats = FlightSeat.objects.filter(flight=flight).order_by("price")
    return render(
        request,
        "flights/flight_detail.html",
        {"flight": flight, "seats": seats},
    )
