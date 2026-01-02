# core/urls.py  (AGREGAR nuevo archivo)
from django.urls import path
from . import views
from .views import index

urlpatterns = [
    path('', views.health_check, name='core-health'),
    path('', index, name='home'),
    
    
]
