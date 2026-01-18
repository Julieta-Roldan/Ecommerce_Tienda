from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from tienda.models import Producto
from .models import Carrito, ItemCarrito
from django.shortcuts import render 
from django.shortcuts import redirect

def obtener_carrito(request):
    """
    Devuelve el carrito asociado a la sesión actual.
    Si no existe, lo crea.
    """
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    carrito, _ = Carrito.objects.get_or_create(
        session_key=session_key
    )

    return carrito





def agregar_producto(request, producto_id):
    carrito = obtener_carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)

    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )

    if not creado:
        item.cantidad += 1
        item.save()

    # 👉 ACÁ ESTÁ LA CLAVE
    return redirect('carrito_ver')

# def ver_carrito(request):
#     items = []
#     total = 0

#     if request.session.session_key:
#         carrito = Carrito.objects.filter(
#             session_key=request.session.session_key
#         ).first()

#         if carrito:
#             items = carrito.items.select_related("producto")
#             total = carrito.total()

#     return render(request, "carrito/carrito.html", {
#         "items": items,
#         "total": total
#     })


def ver_carrito(request):
    items = []
    total = 0

    if request.session.session_key:
        carrito = Carrito.objects.filter(
            session_key=request.session.session_key
        ).first()

        if carrito:
            items = carrito.items.select_related("producto")
            total = carrito.total()

    return render(request, "carrito/carrito.html", {
        "items": items,
        "total": total
    })


def eliminar_producto(request, producto_id):
    """
    Elimina un producto del carrito.
    """
    carrito = obtener_carrito(request)

    item = ItemCarrito.objects.filter(
        carrito=carrito,
        producto_id=producto_id
    ).first()

    if item:
        item.delete()
    return redirect('carrito_ver')

    return redirect('carrito_ver')



def sumar_producto(request, producto_id):
    carrito = obtener_carrito(request)

    item = get_object_or_404(
        ItemCarrito,
        carrito=carrito,
        producto_id=producto_id
    )

    # no pasar stock
    if item.producto.stock > item.cantidad:
        item.cantidad += 1
        item.save()

    return redirect("carrito_ver")


def restar_producto(request, producto_id):
    carrito = obtener_carrito(request)

    item = get_object_or_404(
        ItemCarrito,
        carrito=carrito,
        producto_id=producto_id
    )

    item.cantidad -= 1

    if item.cantidad <= 0:
        item.delete()
    else:
        item.save()

    return redirect("carrito_ver")
