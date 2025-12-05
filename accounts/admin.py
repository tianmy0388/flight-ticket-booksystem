# from django.contrib import admin
#
# # Register your models here.
from django.contrib import admin
from .models import PassengerProfile


@admin.register(PassengerProfile)
class PassengerProfileAdmin(admin.ModelAdmin):
    list_display = ("real_name", "user", "phone", "email")
    search_fields = ("real_name", "phone", "email", "id_card_no")
