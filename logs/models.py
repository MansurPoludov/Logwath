from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class LogFile(models.Model):
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    file = models.FileField(upload_to="logs/")
    uploaded_at = models.DateTimeField(auto_now=True)

class LogEntry(models.Model):
    logfile = models.ForeignKey(LogFile , on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    level = models.CharField(max_length=20)
    message = models.TextField()
    is_anomaly = models.BooleanField(default=False)
    source = models.CharField(max_length=50 , default="unknow"),
    raw = models.TextField(null=True, blank=True)



#Дополнил модель для
class AuditLog(models.Model):
    user = models.ForeignKey(User , on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at} | {self.user} | {self.action}"

