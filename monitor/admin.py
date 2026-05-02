from django.contrib import admin
from .models import Device, ElectricalData

admin.site.register(Device)
admin.site.register(ElectricalData)