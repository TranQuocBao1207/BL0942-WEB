from django.urls import path
from .views import receive_data, latest_data

urlpatterns = [
    path('api/data/', receive_data),
    path('api/latest/', latest_data),
]