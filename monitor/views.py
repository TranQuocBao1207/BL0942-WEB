from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import requests
import re

from .models import Device, ElectricalData


# ===== GOOGLE SHEET =====
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwpplGHbOVB-bWSGARAdzfYKfPyTeXQ13WTNj3oTTMJHmQ0oFuuizdlq-QtNVN5XQhm/exec"


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

    # thêm thiết bị
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

            # tìm device
            device = Device.objects.filter(device_id=device_id).first()
            if not device:
                return JsonResponse({"status": "error", "message": "device not found"})

            # ===== LƯU DB =====
            ElectricalData.objects.create(
                device=device,
                voltage=body.get("voltage", 0),
                current=body.get("current", 0),
                power=body.get("power", 0),
                energy=body.get("energy", 0)
            )

            # ===== GỬI GOOGLE SHEET =====
            try:
                requests.post(
                    GOOGLE_SCRIPT_URL,
                    json=body,
                    timeout=2
                )
            except Exception as e:
                print("Sheet error:", e)  # chỉ log, không crash

            return JsonResponse({"status": "ok"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "invalid request"})


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
    

def energy_chart_data(request):

    SHEET_ID = "ID_GOOGLE_SHEET_CỦA_BẠN"

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json"

    try:
        response = requests.get(url)

        text = response.text

        json_text = re.search(r'google\.visualization\.Query\.setResponse\((.*)\);', text).group(1)

        import json

        data = json.loads(json_text)

        sheets = data['table']['rows']

        labels = []
        values = []

        # đọc từng sheet theo ngày
        ss_url = f"https://spreadsheets.google.com/feeds/worksheets/{SHEET_ID}/public/full?alt=json"

        ws = requests.get(ss_url).json()

        entries = ws['feed']['entry']

        for entry in entries:

            title = entry['title']['$t']

            # chỉ đọc sheet dạng yyyy-mm-dd
            if re.match(r'^\\d{4}-\\d{2}-\\d{2}$', title):

                try:
                    csv_url = f"https://docs.google.com/spreadsheets/d/1uju0s2W0iwLlfkBM2eHt-RS9TvsRAbrij437THnmI_8/gviz/tq?tqx=out:csv&sheet={title}"

                    csv_data = requests.get(csv_url).text

                    rows = csv_data.splitlines()

                    total = 0

                    if len(rows) > 1:

                        last = rows[-1].split(',')

                        # cột Total kWh = cột 8
                        total = float(last[7])

                    labels.append(title)
                    values.append(round(total, 3))

                except:
                    pass

        return JsonResponse({
            "labels": labels,
            "values": values
        })

    except Exception as e:

        return JsonResponse({
            "labels": [],
            "values": [],
            "error": str(e)
        })