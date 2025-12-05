# from django.db import models
#
# # Create your models here.
from django.db import models
from django.contrib.auth.models import User


class PassengerProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    real_name = models.CharField(max_length=50)
    id_card_no = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.real_name} ({self.user.username})"
