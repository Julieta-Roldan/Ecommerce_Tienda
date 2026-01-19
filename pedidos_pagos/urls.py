from django.urls import path
from . import views
from pedidos_pagos.views import crear_pedido_desde_carrito


    # Crear pedido desde carrito (BOTÓN FINALIZAR COMPRA)
urlpatterns = [
    path(
        "crear-desde-carrito/",
        crear_pedido_desde_carrito,
        name="crear_pedido_desde_carrito"
    ),
    # Mercado Pago
    path(
        'pagar/<int:pedido_id>/',
        views.pagar_pedido,
        name='pagar_pedido'
    ),

    path(
        'confirmar-pago/<int:pago_id>/',
        views.confirmar_pago,
        name='confirmar_pago'
    ),

    path(
        'checkout/',
        views.checkout_cliente_externo,
        name='checkout_externo'
    ),

    path(
        'exito/',
        views.pedido_exito,
        name='pedido_exito'
    ),
]
