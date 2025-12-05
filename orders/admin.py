# from django.contrib import admin
#
# # Register your models here.
from django.contrib import admin
from .models import TicketOrder, RefundRecord


@admin.register(TicketOrder)
class TicketOrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "user", "flight", "total_amount", "status", "paid_at")
    list_filter = ("status",)
    search_fields = ("order_no", "user__username")


@admin.register(RefundRecord)
class RefundRecordAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "refund_amount", "refund_fee", "approve_time")
