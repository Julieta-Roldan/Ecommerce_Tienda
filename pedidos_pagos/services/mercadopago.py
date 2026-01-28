# import mercadopago
# from django.conf import settings

# print("MP TOKEN:", settings.MERCADOPAGO_ACCESS_TOKEN)

# def crear_preferencia_pago(pedido):
#     sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

#     items = []
#     for item in pedido.items.all():
#         items.append({
#             "title": item.nombre_producto,
#             "quantity": item.cantidad,
#             "unit_price": float(item.precio_unitario),
#             "currency_id": "ARS",
#         })

#     # preference_data = {
#     #     "items": items,
#     #     "external_reference": str(pedido.id),
#     #     #"notification_url": "http://localhost:8000/webhooks/mercadopago/",
#     #     "back_urls": {
#     #         "success": "http://localhost:8000/pago-exitoso/",
#     #         "failure": "http://localhost:8000/pago-fallido/",
#     #         "pending": "http://localhost:8000/pago-pendiente/",
#     #     },
#     #     "auto_return": "approved",
#     # }
#     preference_data = {
#     "items": items,
#     "external_reference": str(pedido.id),
# }

#     preference = sdk.preference().create(preference_data)
#     return preference["response"]
import mercadopago
from django.conf import settings

print("MP TOKEN:", settings.MERCADOPAGO_ACCESS_TOKEN)

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

    # preference_data = {
    #     "items": items,
    #     "external_reference": str(pedido.id),
    #     #"notification_url": "http://localhost:8000/webhooks/mercadopago/",
    #     "back_urls": {
    #         "success": "http://localhost:8000/pago-exitoso/",
    #         "failure": "http://localhost:8000/pago-fallido/",
    #         "pending": "http://localhost:8000/pago-pendiente/",
    #     },
    #     "auto_return": "approved",
    # }
# import mercadopago
# from django.conf import settings

# def crear_preferencia_pago(pedido):
#     sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

#     preference_data = {
#         "items": [
#             {
#                 "title": "Producto de prueba",
#                 "quantity": 1,
#                 "unit_price": 100.0,
#                 "currency_id": "ARS",
#             }
#         ]
#     }

#     preference = sdk.preference().create(preference_data)

#     print("RESPUESTA MERCADO PAGO ↓↓↓")
#     print(preference)

#     return preference.get("response")

import requests
from django.conf import settings

MP_PREFERENCES_URL = "https://api.mercadopago.com/checkout/preferences"


def crear_preferencia_pago(pedido):
    headers = {
        "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    items = []
    for item in pedido.items.all():
        items.append({
            "title": item.nombre_producto,
            "quantity": item.cantidad,
            "unit_price": float(item.precio_unitario),
            "currency_id": "ARS",
        })

    payload = {
        "items": items,
        # importante en sandbox unificado
        "binary_mode": True,
    }

    response = requests.post(
        MP_PREFERENCES_URL,
        json=payload,
        headers=headers,
        timeout=10,
    )

    print("STATUS MP:", response.status_code)
    print("RESPUESTA MP:", response.text)

    if response.status_code not in (200, 201):
        return None

    return response.json()
