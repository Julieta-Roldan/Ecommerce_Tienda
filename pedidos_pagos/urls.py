# pedidos_pagos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 1. El checkout UNIFICADO (donde pones mail y tel)
    path('checkout/', views.checkout_view, name='checkout'),

    # 2. Mercado Pago
    path('pagar/<int:pedido_id>/', views.pagar_pedido, name='pagar_pedido'),
    
    # 3. Webhooks / Confirmación
    path('confirmar-pago/<int:pago_id>/', views.confirmar_pago, name='confirmar_pago'),
    path('exito/', views.pedido_exito, name='pedido_exito'),

    # 4. Esta ruta la mantenemos solo si la usas para otra cosa, 
    # pero el botón del carrito ahora irá directo al checkout
    path('crear-desde-carrito/', views.crear_pedido_desde_carrito, name="crear_pedido_desde_carrito"),
]