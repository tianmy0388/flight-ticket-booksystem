# from django.db import models
#
# # Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import PassengerProfile
from flights.models import Flight, FlightSeat


class OrderStatus(models.TextChoices):
    PAID = "PAID", "已支付"
    CANCELLED = "CANCELLED", "已取消"
    REFUNDING = "REFUNDING", "退票中"
    REFUNDED = "REFUNDED", "已退票"


class TicketOrder(models.Model):
    order_no = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    profile = models.ForeignKey(
        PassengerProfile, on_delete=models.PROTECT, related_name="orders"
    )
    flight = models.ForeignKey(
        Flight, on_delete=models.PROTECT, related_name="orders"
    )
    seat = models.ForeignKey(
        FlightSeat, on_delete=models.PROTECT, related_name="orders"
    )

    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PAID
    )

    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    def mark_paid(self):
        self.status = OrderStatus.PAID
        self.paid_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.order_no} - {self.flight.flight_no}"


class RefundStatus(models.TextChoices):
    PENDING = "PENDING", "待审核"
    APPROVED = "APPROVED", "已同意"
    REJECTED = "REJECTED", "已拒绝"


class RefundRecord(models.Model):
    order = models.OneToOneField(
        TicketOrder, on_delete=models.CASCADE, related_name="refund_record"
    )
    request_time = models.DateTimeField(auto_now_add=True)
    approve_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=RefundStatus.choices, default=RefundStatus.PENDING
    )
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Refund for {self.order.order_no} - {self.status}"
