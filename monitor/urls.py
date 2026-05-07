from django.urls import path
from .views import receive_data, latest_data
from .views import energy_chart_data

urlpatterns = [
    path('api/data/', receive_data),
    path('api/latest/', latest_data),
    path('api/energy-chart/', energy_chart_data),
]