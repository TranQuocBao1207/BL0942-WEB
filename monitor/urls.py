from django.urls import path
from .views import receive_data

urlpatterns = [
    path('api/data/', receive_data),
]