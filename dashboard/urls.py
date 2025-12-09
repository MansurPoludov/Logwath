from django.urls import path
from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),  # главная страница после логина

]
