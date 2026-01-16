from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from tienda.models import Producto
from .models import Carrito, ItemCarrito
from django.shortcuts import render 

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
    """
    Agrega un producto al carrito de la sesión.
    Si el producto ya existe, incrementa la cantidad.
    """
    carrito = obtener_carrito(request)

    producto = get_object_or_404(Producto, id=producto_id)

    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )

    if not creado:
        item.cantidad += 1
        item.save()

    return JsonResponse({
        "mensaje": f"{producto.nombre} agregado al carrito.",
        "cantidad": item.cantidad
    })


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


#yo
def ver_carrito(request):
    # Datos de prueba para que puedas ver el diseño sin errores de base de datos
    items = [
        {
            'producto': {'nombre': 'Remera de prueba', 'precio': 1500, 'imagen': None},
            'cantidad': 2,
            'subtotal': 3000
        },
        {
            'producto': {'nombre': 'Pantalón de prueba', 'precio': 5000, 'imagen': None},
            'cantidad': 1,
            'subtotal': 5000
        }
    ]
    total = 8000
    return render(request, 'carrito/carrito.html', {'items': items, 'total': total})


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
        return JsonResponse({"mensaje": "Producto eliminado del carrito."})

    return JsonResponse({"mensaje": "El producto no estaba en el carrito."})
