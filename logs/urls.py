from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_log, name="upload_log"),
    path("clear/", views.clear_logs, name="clear_logs"),
    path('activity_log/', views.admin_protected_activity, name='activity_log'),
    path('logs/clear_auditlog/', views.clear_auditlog , name='clear_auditlog')
]
