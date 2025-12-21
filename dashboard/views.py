from django.shortcuts import render, redirect
from numpy.ma.core import anomalies
from logs.models import LogEntry, LogFile
from django.contrib.auth.decorators import login_required
from django.utils.timezone import make_aware
from datetime import datetime

@login_required(login_url='/accounts/login/')
def dashboard(request):
    last_logs = LogFile.objects.filter(user=request.user).order_by("-uploaded_at")[:5]
    entries = LogEntry.objects.filter(logfile__user=request.user)

    # ----- ФИЛЬТРЫ -----
    level = request.GET.get("level")
    logfile = request.GET.get("logfile")
    anomaly = request.GET.get("anomaly")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if level:
        entries = entries.filter(level=level)

    if logfile:
        entries = entries.filter(logfile_id=logfile)

    if anomaly:
        entries = entries.filter(is_anomaly=True)

    if date_from:
        entries = entries.filter(timestamp__gte=make_aware(datetime.fromisoformat(date_from)))

    if date_to:
        entries = entries.filter(timestamp__lte=make_aware(datetime.fromisoformat(date_to)))

    entries = entries.order_by("-timestamp")

    context = {
        "total": entries.count(),
        "errors": entries.filter(level="ERROR").count(),
        "warnings": entries.filter(level="WARNING").count(),
        "anomaly": entries.filter(is_anomaly=True).count(),
        "last_logs": last_logs,
        "entries": entries[:50],

        # ⬇️ для сохранения значений в форме
        "selected_level": level,
        "selected_logfile": logfile,
        "date_from": date_from,
        "date_to": date_to,
        "only_anomaly": anomaly,
    }

    return render(request, "dashboard.html", context)



