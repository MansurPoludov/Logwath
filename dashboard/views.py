from django.shortcuts import render, redirect

from numpy.ma.core import anomalies

from logs.models import LogEntry, LogFile
from django.contrib.auth.decorators import login_required


@login_required(login_url='/accounts/login/')
def dashboard(request):
    last_logs = LogFile.objects.filter(user=request.user).order_by("-uploaded_at")[:5]
    entries = LogEntry.objects.filter(logfile__user=request.user)
    level = request.GET.get("level")
    only_anomaly = request.GET.get("anomaly")

    if level:
        entries = entries.filter(level=level)
    if only_anomaly:
        entries = entries.filter(is_anomaly=True)
    entries = entries.order_by("-timestamp")

    total = entries.count()
    errors = entries.filter(level="ERROR").count()
    warnings = entries.filter(level="WARNING").count()
    anomaly = entries.filter(is_anomaly=True).count()
    context = {

        "total": total,
        "errors": errors,
        "warnings": warnings,
        "anomaly": anomaly,
        "last_logs": last_logs,
        "entries": entries[:50],

    }

    return render(request, "dashboard.html", context)


