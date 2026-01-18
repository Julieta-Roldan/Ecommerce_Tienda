# carrito/urls.py
from django.urls import path
from . import views
urlpatterns = [
    # rutas de la app 'carrito' se agregarán aquí
    path('agregar/<int:producto_id>/', views.agregar_producto, name='carrito_agregar'),
    path('ver/', views.ver_carrito, name='carrito_ver'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='carrito_eliminar'),
     path('sumar/<int:producto_id>/', views.sumar_producto, name='carrito_sumar'),
    path('restar/<int:producto_id>/', views.restar_producto, name='carrito_restar'),
]
