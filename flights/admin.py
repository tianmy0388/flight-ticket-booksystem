# from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Airport, Flight, FlightSeat


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "city", "country")
    search_fields = ("code", "name", "city")


class FlightSeatInline(admin.TabularInline):
    model = FlightSeat
    extra = 1


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "flight_no",
        "airline",
        "depart_airport",
        "arrive_airport",
        "depart_time",
        "status",
    )
    list_filter = ("status", "depart_airport", "arrive_airport")
    inlines = [FlightSeatInline]
