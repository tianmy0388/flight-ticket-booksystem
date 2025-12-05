# from django.db import models

# Create your models here.
from django.db import models


class Airport(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.city} - {self.name} ({self.code})"


class FlightStatus(models.TextChoices):
    ON_SALE = "ON_SALE", "在售"
    CANCELLED = "CANCELLED", "已取消"
    FINISHED = "FINISHED", "已结束"


class Flight(models.Model):
    flight_no = models.CharField(max_length=20)
    airline = models.CharField(max_length=50)
    plane_type = models.CharField(max_length=50)

    depart_airport = models.ForeignKey(
        Airport, related_name="depart_flights", on_delete=models.PROTECT
    )
    arrive_airport = models.ForeignKey(
        Airport, related_name="arrive_flights", on_delete=models.PROTECT
    )

    depart_time = models.DateTimeField()
    arrive_time = models.DateTimeField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20, choices=FlightStatus.choices, default=FlightStatus.ON_SALE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.flight_no} {self.depart_airport.code}->{self.arrive_airport.code}"


class CabinClass(models.TextChoices):
    ECONOMY = "ECONOMY", "经济舱"
    BUSINESS = "BUSINESS", "公务舱"
    FIRST = "FIRST", "头等舱"


class FlightSeat(models.Model):
    flight = models.ForeignKey(Flight, related_name="seats", on_delete=models.CASCADE)
    cabin_class = models.CharField(max_length=20, choices=CabinClass.choices)
    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("flight", "cabin_class")

    def __str__(self):
        return f"{self.flight.flight_no}-{self.get_cabin_class_display()}"
