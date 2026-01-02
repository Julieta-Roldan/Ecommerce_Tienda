from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.crear_pedido_desde_carrito, name='crear_pedido'),
    path('mis_pedidos/', views.listar_pedidos_usuario, name='listar_pedidos'),
    path('detalle/<int:pedido_id>/', views.ver_detalle_pedido, name='detalle_pedido'),
    path('checkout_externo/', views.checkout_cliente_externo, name='checkout_externo'),
]
