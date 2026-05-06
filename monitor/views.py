from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from .models import Device, ElectricalData


# ===== LOGIN =====
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("/dashboard/")
        else:
            return render(request, "login.html", {
                "error": "Sai tài khoản hoặc mật khẩu"
            })

    return render(request, "login.html")


# ===== REGISTER =====
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password != confirm:
            return render(request, "register.html", {
                "error": "Mật khẩu không khớp"
            })

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {
                "error": "Tài khoản đã tồn tại"
            })

        User.objects.create_user(username=username, password=password)
        return redirect("/")

    return render(request, "register.html")


# ===== LOGOUT =====
def logout_view(request):
    logout(request)
    return redirect("/")


# ===== DASHBOARD =====
@login_required
def dashboard(request):
    user = request.user
    devices = Device.objects.filter(user=user)

    # THÊM THIẾT BỊ
    if request.method == "POST":
        name = request.POST.get("name")
        device_id = request.POST.get("device_id")

        if name and device_id:
            new_device = Device.objects.create(
                user=user,
                name=name,
                device_id=device_id
            )
            return redirect(f"/dashboard/?device={new_device.id}")

    # CHỌN THIẾT BỊ
    selected_device = None
    device_param = request.GET.get("device")

    if device_param:
        try:
            selected_device = Device.objects.get(id=device_param, user=user)
        except Device.DoesNotExist:
            selected_device = None

    if not selected_device and devices.exists():
        selected_device = devices.first()

    return render(request, "dashboard.html", {
        "devices": devices,
        "selected_device": selected_device
    })


# ===== DELETE DEVICE =====
@login_required
def delete_device(request, id):
    device = get_object_or_404(Device, id=id, user=request.user)
    device.delete()
    return redirect("/dashboard/")


# ===== API NHẬN DATA TỪ ESP32 =====
@csrf_exempt
def receive_data(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)

            device_id = body.get("device_id")

            if not device_id:
                return JsonResponse({"status": "error", "message": "missing device_id"})

            # 🔥 FIX: không crash nếu device không tồn tại
            device = Device.objects.filter(device_id=device_id).first()
            if not device:
                return JsonResponse({"status": "error", "message": "device not found"})

            ElectricalData.objects.create(
                device=device,
                voltage=body.get("voltage", 0),
                current=body.get("current", 0),
                power=body.get("power", 0),
                energy=body.get("energy", 0)
            )

            return JsonResponse({"status": "ok"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "invalid request"})


# ===== API LẤY DATA REALTIME =====
def latest_data(request):
    device_id = request.GET.get("device_id")

    if not device_id:
        return JsonResponse({"status": "error", "message": "missing device_id"})

    try:
        device = Device.objects.filter(device_id=device_id).first()

        if not device:
            return JsonResponse({"status": "error", "message": "device not found"})

        latest = ElectricalData.objects.filter(
            device=device
        ).order_by('-created_at').first()

        if latest:
            return JsonResponse({
                "status": "ok",
                "voltage": float(latest.voltage),
                "current": float(latest.current),
                "power": float(latest.power),
                "energy": float(latest.energy)
            })

        return JsonResponse({"status": "no_data"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/XXXX/exec"

@csrf_exempt
def receive_data(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # gửi sang Google Sheet
            requests.post(GOOGLE_SCRIPT_URL, json=data, timeout=3)

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "error", "msg": str(e)})

    return JsonResponse({"status": "invalid"})