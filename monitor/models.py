from django.db import models
from django.contrib.auth.models import User

class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ElectricalData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    energy = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 bắt buộc

    class Meta:
        ordering = ['-created_at']  # 🔥 mới nhất luôn đứng đầu