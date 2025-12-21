from django.shortcuts import render, redirect
from .models import  LogFile , LogEntry , AuditLog
from .services import analyze_log
from  django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.utils import  timezone

# Create your views here.

def upload_log(request):
    if request.method == "POST":
        file = request.FILES["logfile"]


        log_obj = LogFile.objects.create(user = request.user , file = file)
        entries = analyze_log(log_obj.file.path)

        for ts, level, msg, anomaly in entries:
            LogEntry.objects.create(
                logfile = log_obj,
                timestamp = ts,
                level = level,
                message = msg ,
                is_anomaly = anomaly)
        AuditLog.objects.create(
            user=request.user,
            action=f'uploaded_log_file: {file.name}',
            ip=get_client_ip(request)
        )

        return redirect("dashboard")
    return render(request , "upload_log.html")


@login_required()
def clear_logs(request):
    if request.method == 'POST':
        for lf in LogFile.objects.filter(user=request.user):
            lf.file.delete(save=False)
        LogEntry.objects.filter(logfile__user=request.user).delete()
        LogFile.objects.filter(user=request.user).delete()
        AuditLog.objects.create(
            user=request.user,
            action='logs_cleared',
            ip=get_client_ip(request)
        )

        messages.success(request,"Все ваши логи успешно удалены.")
        return redirect('dashboard')
    else:
        messages.error(request,"Неверный метод запроса.")
        return redirect("dashboard")

@login_required
def clear_auditlog(request):
    if request.method != 'POST':
        messages.error(request, "Неверный метод запроса.")
        return redirect('activity_log')
    if not request.user.is_staff and not request.is_superuser:
        messages.error(request, 'Доступ запрещён. Только админ может очистить журнал активности.')
        return redirect('activity_log')
    AuditLog.objects.all().delete()

    AuditLog.objects.create(
        user = request.user,
        action='auditlog_cleared_by_admin',
        ip=get_client_ip(request)
    )
    messages.success(request, "Журнал активности успешно очищен.")
    return redirect('activity_log')




def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

@login_required(login_url='login')
def admin_protected_activity(request):
    """
    Если в сессии есть admin_verified (и не просрочен) — показываем activity.
    Иначе — показываем форму запроса админ-логина.
    """
    # --- Проверка таймаута (опция) ---
    verified = request.session.get('admin_verified', False)
    verified_at = request.session.get('admin_verified_at' , False)
    ADMIN_VERIFY_TTL_SECONDS = 60 * 10

    if verified and verified_at:
        try:
            dt = timezone.datetime.fromisoformat(verified_at)
            dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            if (timezone.now() - dt).total_seconds() > ADMIN_VERIFY_TTL_SECONDS:
                request.session.pop('admin_verified', None)
                request.session.pop('admin_verified_at', None)
                verified = False
        except Exception:
            request.session.pop('admin_verified', None)
            request.session.pop('admin_verified_at', None)
            verified = False

    if verified:
        logs = AuditLog.objects.select_related('user').order_by('-created_at')[:500]
        return render(request, 'activity_log.html', {'logs': logs})

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        ip = get_client_ip(request)
        if user is not None and (user.is_staff or user.is_superuser):
            request.session['admin_verified'] = True
            request.session['admin_verified_at'] = timezone.now().isoformat()

            try:
                AuditLog.objects.create(user=user, action='admin_verified', ip=ip)
            except Exception:
                pass
            # показать отчёт после проверки
            logs = AuditLog.objects.select_related('user').order_by('-created_at')[:500]
            return render(request, 'activity_log.html', {'logs': logs})
        else:
            # невалидные данные или не админ
            messages.error(request, 'Доступ разрешён только для администратора.')
            try:
                AuditLog.objects.create(user=user if user and user.is_authenticated else None,
                                        action='admin_verify_failed',
                                        ip=ip)
            except Exception:
                pass
            return render(request, 'admin_auth.html', {'error': 'Доступ разрешён только для администратора.'})

            # GET — показать форму запроса админ-логина
    return render(request, 'admin_auth.html')