# tienda/urls.py
from django.urls import path
from .views import (
    listar_productos, obtener_producto, crear_producto,
    actualizar_producto, eliminar_producto
)
from .views import catalogo
from . import views


urlpatterns = [
    path('productos/', listar_productos),
    path('productos/<int:producto_id>/', obtener_producto),
    path('productos/crear/', crear_producto),
    path('productos/<int:producto_id>/actualizar/', actualizar_producto),
    path('productos/<int:producto_id>/eliminar/', eliminar_producto),
    path('catalogo/', catalogo, name='catalogo'),
    path('buscar/', views.vista_busqueda, name='buscar_productos'),
    
]
