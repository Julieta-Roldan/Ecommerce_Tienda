from django.urls import path
from . import views

urlpatterns = [
    # Cliente externo: crea pedido con JSON
    path(
        'checkout/',
        views.checkout_cliente_externo,
        name='checkout_externo'
    ),

    # Crear preferencia de pago Mercado Pago
    path(
        'pagar/<int:pedido_id>/',
        views.pagar_pedido,
        name='pagar_pedido'
    ),

    # Confirmar pago (webhook o simulación)
    path(
        'confirmar-pago/<int:pago_id>/',
        views.confirmar_pago,
        name='confirmar_pago'
    ),
]
