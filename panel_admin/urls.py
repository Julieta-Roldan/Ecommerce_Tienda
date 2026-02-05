# panel_admin/urls.py
from django.urls import path
from . import views

app_name = 'panel_admin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Autenticación
    path('login/', views.login_panel, name='login'),
    path('logout/', views.logout_panel, name='logout'),
    
    # Productos
    path('productos/', views.productos_lista, name='productos'),
    path('productos/nuevo/', views.producto_nuevo, name='producto_nuevo'),
    path('productos/editar/<int:id>/', views.producto_editar, name='producto_editar'),
    path('productos/eliminar/<int:id>/', views.producto_eliminar, name='producto_eliminar'),
    
    # Talles y Colores rápidos
    path('talles/agregar-rapido/', views.agregar_talle_rapido, name='agregar_talle_rapido'),
    path('colores/agregar-rapido/', views.agregar_color_rapido, name='agregar_color_rapido'),
    
    # Eliminar talles y colores
    path('talles/eliminar-rapido/', views.eliminar_talle_rapido, name='eliminar_talle_rapido'),
    path('colores/eliminar-rapido/', views.eliminar_color_rapido, name='eliminar_color_rapido'),
    
    # Categorías (NUEVO)
    path('categorias/', views.categorias_lista, name='categorias'),
    path('categorias/nueva/', views.categoria_nueva, name='categoria_nueva'),
    path('categorias/editar/<int:id>/', views.categoria_editar, name='categoria_editar'),
    path('categorias/eliminar/<int:id>/', views.categoria_eliminar, name='categoria_eliminar'),
    
    # Pedidos
    path('pedidos/', views.pedidos_lista, name='pedidos'),
    path('pedidos/<int:id>/', views.pedido_detalle, name='pedido_detalle'),
    path('pedidos/<int:id>/cambiar-estado/', views.cambiar_estado_pedido, name='cambiar_estado'),
    path('pedidos/<int:pedido_id>/eliminar/', views.pedido_eliminar, name='pedido_eliminar'),
    
    # Usuarios/Empleados (NUEVO)
    path('usuarios/', views.usuarios_lista, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_nuevo, name='usuario_nuevo'),
    path('usuarios/editar/<int:id>/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/cambiar-estado/<int:id>/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
    path('usuarios/eliminar/<int:id>/', views.usuario_eliminar, name='usuario_eliminar'),
    # Estadísticas
    path('estadisticas/', views.estadisticas, name='estadisticas'),



]