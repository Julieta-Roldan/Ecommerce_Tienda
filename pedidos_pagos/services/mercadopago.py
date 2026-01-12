import mercadopago
from django.conf import settings


def crear_preferencia_pago(pedido):
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    items = []
    for item in pedido.items.all():
        items.append({
            "title": item.nombre_producto,
            "quantity": item.cantidad,
            "unit_price": float(item.precio_unitario),
            "currency_id": "ARS",
        })

    preference_data = {
        "items": items,
        "external_reference": str(pedido.id),
        "notification_url": "http://localhost:8000/webhooks/mercadopago/",
        "back_urls": {
            "success": "http://localhost:8000/pago-exitoso/",
            "failure": "http://localhost:8000/pago-fallido/",
            "pending": "http://localhost:8000/pago-pendiente/",
        },
        "auto_return": "approved",
    }

    preference = sdk.preference().create(preference_data)
    return preference["response"]
