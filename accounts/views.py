from django.shortcuts import render, redirect
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages

from accounts.forms import LoginForm, RegisterForm
from logs.models import AuditLog


def login_view(request):
    if request.user.is_authenticated:
        return request('dashboard')

    form = LoginForm(request.POST or None)
    next_url = request.GET.get('next') or request.POST.get('next') or None
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # важно! создаёт сессию
            AuditLog.objects.create(
                user=user,
                action='login_success',
                ip=request.META.get('REMOTE_ADDR')
            )
            messages.success(request , 'Вы вошли в систему.')
            return redirect(next_url or 'dashboard')
        else:
            AuditLog.objects.create(
                user=None,
                action=f'login_failed ({username})',
                ip=request.META.get('REMOTE_ADDR')
            )
            messages.error(request, "Неверный логин или пароль")

    return render(request, "login.html", {'form': form , 'next':next_url , "hide_sidebar": True},)

def logout_view(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            # ✅ ЛОГИРУЕМ ДО logout()
            AuditLog.objects.create(
                user=request.user,
                action='logout',
                ip=request.META.get('REMOTE_ADDR')
            )
            # ✅ чистим админ-сессию
        request.session.pop('admin_verified', None)
        request.session.pop('admin_verified_at', None)
        # ✅ завершаем сессию пользователя
        logout(request)
        messages.success(request , 'Вы вышли из системы.')
        return redirect('login')
    return redirect('dashboard')

def register_views(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user=form.save()
            AuditLog.objects.create(
                user=user,
                action='user_registered',
                ip=request.META.get('REMOTE_ADDR')
            )
            messages.success(request , 'Регистрация прошла успешно. Теперь войдите.')
            return redirect('login')
        else:
            for field , errors in form.errors.items():
                for error in errors:
                    messages.error(request , error)
    return render(request , 'register.html' , {'form':form , 'hide_sidebar': True})