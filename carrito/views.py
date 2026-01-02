from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from tienda.models import Producto
from .models import Carrito, ItemCarrito


@login_required
def agregar_producto(request, producto_id):

    # Buscar producto o devolver error 404
    producto = get_object_or_404(Producto, id=producto_id)

    # Obtener o crear carrito del usuario
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    # Buscar si el producto ya está en el carrito
    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )

    # Si ya estaba, solo se incrementa la cantidad
    if not creado:
        item.cantidad += 1
        item.save()

    return JsonResponse({
        "mensaje": f"{producto.nombre} agregado al carrito.",
        "cantidad_actual": item.cantidad
    })


@login_required
def ver_carrito(request):

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    datos = {
        "usuario": request.user.username,
        "total": carrito.total,
        "items": [
            {
                "producto": item.producto.nombre,
                "cantidad": item.cantidad,
                "subtotal": item.subtotal
            }
            for item in carrito.items.all()
        ]
    }

    return JsonResponse(datos)


@login_required
def eliminar_producto(request, producto_id):

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    item = ItemCarrito.objects.filter(
        carrito=carrito,
        producto_id=producto_id
    ).first()

    if item:
        item.delete()
        return JsonResponse({"mensaje": "Producto eliminado correctamente."})

    return JsonResponse({"mensaje": "El producto no estaba en el carrito."})
