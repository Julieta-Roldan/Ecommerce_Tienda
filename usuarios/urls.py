# usuarios/urls.py
from django.urls import path
from . import views
from .views import mi_perfil

urlpatterns = [
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/<int:id>/', views.detalle_empleado, name='detalle_empleado'),
    path('empleados/<int:id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('mi-perfil/', mi_perfil),
]
