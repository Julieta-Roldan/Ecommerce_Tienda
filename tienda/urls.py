# tienda/urls.py
from django.urls import path
from .views import (
    listar_productos, obtener_producto, crear_producto,
    actualizar_producto, eliminar_producto
)
from .views import catalogo
from . import views


urlpatterns = [
    # Ruta para ver TODO el catálogo
    path('catalogo/', views.catalogo, name='catalogo'),
    
    # NUEVA RUTA: Para filtrar por categoría (ej: catalogo/pantalones/)
    path('catalogo/<str:nombre_categoria>/', views.catalogo, name='catalogo_categoria'),
    
    path('buscar/', views.vista_busqueda, name='buscar_productos'),
    path('producto/<int:id>/', views.producto_detalle, name='producto_detalle'),
]
