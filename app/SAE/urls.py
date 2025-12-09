"""
URL Configuration for SAE Application
"""

from django.urls import path
from . import views

app_name = 'sae'

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.healthcheck, name='healthcheck'),
    path('demo/', views.demo, name='demo'),
]
