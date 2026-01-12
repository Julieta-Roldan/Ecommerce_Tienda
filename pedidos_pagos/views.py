import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db import transaction

from tienda.models import Producto
from .models import Pedido, ItemPedido, Pago
from .services.mercadopago import crear_preferencia_pago


@csrf_exempt
def checkout_cliente_externo(request):
    """
    Cliente externo envía JSON con items y datos de contacto.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    data = json.loads(request.body.decode("utf-8"))

    email = data.get("email")
    telefono = data.get("telefono")
    items = data.get("items")

    if not items:
        return JsonResponse({"error": "No hay items"}, status=400)

    pedido = Pedido.objects.create(
        email=email,
        telefono=telefono,
        estado="pendiente"
    )

    total = 0

    for item in items:
        producto = get_object_or_404(Producto, id=item["producto_id"])
        cantidad = item.get("cantidad", 1)

        ItemPedido.objects.create(
            pedido=pedido,
            producto=producto,
            nombre_producto=producto.nombre,
            precio_unitario=producto.precio,
            cantidad=cantidad
        )

        total += producto.precio * cantidad

    return JsonResponse({
        "mensaje": "Pedido creado",
        "pedido_id": pedido.id,
        "total": float(total)
    })


@csrf_exempt
def pagar_pedido(request, pedido_id):
    """
    Crea el pago y la preferencia de Mercado Pago.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if pedido.estado != "pendiente":
        return JsonResponse(
            {"error": "Este pedido no puede pagarse"},
            status=400
        )

    pago = Pago.objects.create(
        pedido=pedido,
        monto=pedido.total,
        metodo="mercadopago",
        estado="pendiente"
    )

    preferencia = crear_preferencia_pago(pedido)

    return JsonResponse({
        "pago_id": pago.id,
        "init_point": preferencia["init_point"],
        "sandbox_init_point": preferencia.get("sandbox_init_point")
    })


@csrf_exempt
@transaction.atomic
def confirmar_pago(request, pago_id):
    """
    Confirmación del pago (webhook o simulación).
    """
    pago = get_object_or_404(Pago, id=pago_id, estado="pendiente")
    pedido = pago.pedido

    for item in pedido.items.all():
        if item.producto.stock < item.cantidad:
            return JsonResponse(
                {"error": f"Stock insuficiente para {item.producto.nombre}"},
                status=400
            )

    for item in pedido.items.all():
        producto = item.producto
        producto.stock -= item.cantidad
        producto.save()

    pago.estado = "aprobado"
    pago.save()

    pedido.estado = "pagado"
    pedido.save()

    return JsonResponse({
        "mensaje": "Pago confirmado",
        "pedido_id": pedido.id
    })
