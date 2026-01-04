from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from carrito.models import Carrito, ItemCarrito
from .models import Pedido, ItemPedido
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Pago
from .services import crear_pedido_desde_carrito

@login_required
def crear_pedido_desde_carrito(request):

    try:
        carrito = Carrito.objects.get(usuario=request.user)
    except Carrito.DoesNotExist:
        return JsonResponse({"error": "El usuario no tiene carrito"}, status=400)

    if carrito.items.count() == 0:
        return JsonResponse({"error": "El carrito está vacío"}, status=400)

    # 1. Crear el pedido
    pedido = Pedido.objects.create(
        usuario=request.user,
        estado='pendiente'
    )

    # 2. Pasar items del carrito al pedido
    for item in carrito.items.all():
        ItemPedido.objects.create(
            pedido=pedido,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=item.producto.precio
        )

    # 3. Vaciar carrito
    carrito.items.all().delete()

    return JsonResponse({
        "mensaje": "Pedido creado correctamente",
        "pedido_id": pedido.id,
        "total": pedido.total
    })



@login_required
def listar_pedidos_usuario(request):

    pedidos = Pedido.objects.filter(usuario=request.user)

    datos = [
        {
            "id": p.id,
            "estado": p.estado,
            "fecha": p.fecha_creacion,
            "total": p.total
        }
        for p in pedidos
    ]

    return JsonResponse({"pedidos": datos})


@login_required
def ver_detalle_pedido(request, pedido_id):

    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    datos = {
        "id": pedido.id,
        "estado": pedido.estado,
        "fecha": pedido.fecha_creacion,
        "total": pedido.total,
        "items": [
            {
                "producto": item.producto.nombre,
                "cantidad": item.cantidad,
                "precio_unitario": item.precio_unitario,
                "subtotal": item.subtotal
            }
            for item in pedido.items.all()
        ]
    }

    return JsonResponse(datos)


@csrf_exempt
def checkout_cliente_externo(request):

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    # Obtener datos enviados en JSON
    data = json.loads(request.body.decode('utf-8'))

    email = data.get("email")
    telefono = data.get("telefono")
    carrito_items = data.get("items")  # el frontend enviará [{"producto_id":1,"cantidad":2}, ...]

    # Validación mínima
    if not email and not telefono:
        return JsonResponse({"error": "Debe proporcionar email o teléfono"}, status=400)

    if not carrito_items:
        return JsonResponse({"error": "Debe enviar items para crear el pedido"}, status=400)

    # Crear pedido sin usuario
    pedido = Pedido.objects.create(
        usuario=None,
        estado="pendiente",
        email_cliente=email,
        telefono_cliente=telefono
    )

    total = 0

    # Crear items del pedido
    for item in carrito_items:
        producto_id = item.get("producto_id")
        cantidad = item.get("cantidad", 1)

        producto = get_object_or_404(Producto, id=producto_id)

        ItemPedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio
        )

        total += producto.precio * cantidad

    return JsonResponse({
        "mensaje": "Pedido externo creado correctamente",
        "pedido_id": pedido.id,
        "total": float(total)
    })


def crear_pago_pendiente(pedido):
    pago = Pago.objects.create(
        pedido=pedido,
        monto=pedido.total,
        estado='pendiente'
    )
    return pago

def confirmar_pago(pago_id, referencia_externa):
    pago = Pago.objects.get(id=pago_id)

    pago.estado = 'aprobado'
    pago.referencia_externa = referencia_externa
    pago.save()

    pedido = pago.pedido
    pedido.estado = 'pagado'
    pedido.save()

def confirmar_pedido(request, carrito_id):
    carrito = get_object_or_404(Carrito, id=carrito_id)

    email = request.POST.get('email')
    telefono = request.POST.get('telefono')

    pedido = crear_pedido_desde_carrito(
        carrito=carrito,
        email=email,
        telefono=telefono
    )

    return JsonResponse({
        'pedido_id': pedido.id,
        'total': pedido.total,
        'estado': pedido.estado
    })
