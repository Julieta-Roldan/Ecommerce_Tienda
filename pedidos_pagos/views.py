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
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages

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




def pagar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if pedido.estado != "pendiente":
        return redirect("pedido_exito")

    # 1️⃣ GET → mostrar página de pago
    if request.method == "GET":
        return render(
            request,
            "pedidos_pagos/pagar_pedido.html",
            {"pedido": pedido}
        )
    if request.method == "POST":
     preferencia = crear_preferencia_pago(pedido)

    if preferencia is None:
        return JsonResponse(
        {
            "error": "Mercado Pago rechazó la preferencia (sandbox / políticas)",
        },
        status=400,
    )

    if "init_point" not in preferencia:
        return JsonResponse(
        {
            "error": "Respuesta inválida de Mercado Pago",
            "respuesta_mp": preferencia,
        },
        status=400,
    )

    return redirect(preferencia["init_point"])


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



@require_POST
@transaction.atomic
def crear_pedido_desde_carrito(request):
    """
    Crea un pedido a partir del carrito actual.
    """
    # 1️⃣ Verificar sesión
    if not request.session.session_key:
        messages.error(request, "No hay sesión activa")
        return redirect('catalogo')

    # 2️⃣ Obtener carrito
    carrito = Carrito.objects.filter(
        session_key=request.session.session_key
    ).first()

    if not carrito or not carrito.items.exists():
        messages.error(request, "Tu carrito está vacío")
        return redirect('carrito_ver')

    # 3️⃣ Verificar si ya tiene un pedido pendiente
    if hasattr(carrito, 'pedido'):
        pedido_existente = carrito.pedido
        if pedido_existente.estado == 'pendiente':
            messages.info(request, "Ya tienes un pedido pendiente")
            return redirect('pagar_pedido', pedido_id=pedido_existente.id)
        # Si el pedido anterior no está pendiente, podemos crear uno nuevo
        # (continuamos con el flujo normal)

    # 4️⃣ Validar stock ANTES de crear nada
    items_con_problemas = []
    for item in carrito.items.select_related('producto'):
        if item.producto.stock < item.cantidad:
            items_con_problemas.append(f"{item.producto.nombre} (stock: {item.producto.stock})")

    if items_con_problemas:
        messages.error(
            request, 
            f"Stock insuficiente: {', '.join(items_con_problemas)}"
        )
        return redirect('carrito_ver')

    try:
        # 5️⃣ Crear pedido
        pedido = Pedido.objects.create(
            carrito=carrito,
            estado='pendiente'
        )

        # 6️⃣ Crear items del pedido
        for item in carrito.items.select_related('producto'):
            producto = item.producto
            
            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                nombre_producto=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=item.cantidad
            )

        messages.success(request, f"Pedido #{pedido.id} creado correctamente")
        
        # 7️⃣ Redirigir al pago
        return redirect('pagar_pedido', pedido_id=pedido.id)

    except Exception as e:
        messages.error(request, f"Error al crear el pedido: {str(e)}")
        return redirect('carrito_ver')

def pedido_exito(request):
    return render(request, 'pedidos_pagos/pedido_exito.html')
# pedidos_pagos/views.py
from django.db import transaction

@transaction.atomic
def checkout_view(request):
    session_key = request.session.session_key
    carrito = Carrito.objects.filter(session_key=session_key).first()

    if not carrito or not carrito.items.exists():
        return redirect('catalogo')

    if request.method == 'POST':
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        total = sum(item.producto.precio * item.cantidad for item in carrito.items.all())

        # SOLUCIÓN AL ERROR UNIQUE: update_or_create
        # Buscamos si el carrito ya tiene un pedido, si existe lo actualizamos, sino lo creamos.
        pedido, created = Pedido.objects.update_or_create(
            carrito=carrito,
            defaults={
                'email': email,
                'telefono': telefono,
                'estado': 'pendiente',
                'total_pago': total # O 'total' según tu modelo
            }
        )

        # Limpiamos los items viejos del pedido para no duplicar si el usuario volvió atrás
        ItemPedido.objects.filter(pedido=pedido).delete()

        # Creamos los items actuales
        for item in carrito.items.all():
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                nombre_producto=item.producto.nombre,
                precio_unitario=item.producto.precio,
                cantidad=item.cantidad
            )

        return redirect('pagar_pedido', pedido_id=pedido.id)

    subtotal = sum(item.producto.precio * item.cantidad for item in carrito.items.all())
    return render(request, 'pedidos_pagos/checkout.html', {
        'carrito': carrito,
        'subtotal': subtotal,
    })