from django.contrib import admin
from django.urls import path, include
from monitor import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitor.urls')),

    path('', views.login_view),
    path('register/', views.register),
    path('logout/', views.logout_view),

    path('dashboard/', views.dashboard),
    path('delete-device/<int:id>/', views.delete_device),

    # 🔥 THÊM DÒNG NÀY
    path('api/data/', views.receive_data),
    path('api/latest-data/', views.latest_data),
]