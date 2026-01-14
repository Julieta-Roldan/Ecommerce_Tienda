import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db import transaction

from tienda.models import Producto
from .models import Pedido, ItemPedido, Pago
from .services.mercadopago import crear_preferencia_pago
from decimal import Decimal
from carrito.models import Carrito, ItemCarrito

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
        producto = get_object_or_404(Producto, id=item.get("producto_id"))
        cantidad = int(item.get("cantidad", 1))

        # ✅ VALIDACIONES CLAVE
        if cantidad <= 0:
            return JsonResponse(
                {"error": "Cantidad inválida"},
                status=400
            )

        if producto.stock < cantidad:
            return JsonResponse(
                {"error": f"Stock insuficiente para {producto.nombre}"},
                status=400
            )

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
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método no permitido"},
            status=405
        )

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
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método no permitido"},
            status=405)
            
            
    pago = get_object_or_404(Pago, id=pago_id, estado="pendiente")
    pedido = pago.pedido

    # 1️⃣ Validar stock ANTES de tocar nada
    for item in pedido.items.all():
        if item.producto.stock < item.cantidad:
            return JsonResponse(
                {"error": f"Stock insuficiente para {item.producto.nombre}"},
                status=400
            )

    # 2️⃣ Descontar stock
    for item in pedido.items.all():
        producto = item.producto
        producto.stock -= item.cantidad
        producto.save()

    # 3️⃣ Marcar pago como aprobado
    pago.estado = "aprobado"
    pago.referencia_externa = f"PAGO-{pago.id}"
    pago.save()

    # 4️⃣ Marcar pedido como pagado
    pedido.estado = "pagado"
    pedido.save()

    return JsonResponse({
        "mensaje": "Pago confirmado correctamente",
        "pedido_id": pedido.id,
        "pago_id": pago.id,
        "estado_pago": pago.estado
    })


@csrf_exempt
def crear_pedido_desde_carrito(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método no permitido"},
            status=405
        )

    if not request.session.session_key:
        return JsonResponse(
            {"error": "No hay carrito activo"},
            status=400
        )

    carrito = Carrito.objects.filter(
        session_key=request.session.session_key
    ).first()

    if not carrito or not carrito.items.exists():
        return JsonResponse(
            {"error": "El carrito está vacío"},
            status=400
        )

    # 🔒 Evitar pedidos duplicados
    if hasattr(carrito, "pedido"):
        return JsonResponse(
            {"error": "Este carrito ya tiene un pedido"},
            status=400
        )

    pedido = Pedido.objects.create(
        carrito=carrito,
        estado="pendiente"
    )

    for item in carrito.items.select_related("producto"):
        producto = item.producto

        if producto.stock < item.cantidad:
            return JsonResponse(
                {"error": f"Stock insuficiente para {producto.nombre}"},
                status=400
            )

        ItemPedido.objects.create(
            pedido=pedido,
            producto=producto,
            nombre_producto=producto.nombre,
            precio_unitario=producto.precio,
            cantidad=item.cantidad
        )

    return JsonResponse({
        "mensaje": "Pedido creado desde carrito",
        "pedido_id": pedido.id,
        "total": float(pedido.total)
    })
