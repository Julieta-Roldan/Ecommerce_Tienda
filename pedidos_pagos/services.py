from carrito.views import obtener_carrito
from .models import Pedido, ItemPedido

def crear_pedido_desde_carrito(request, email=None, telefono=None):
    carrito = obtener_carrito(request)

    if carrito.items.count() == 0:
        raise Exception("El carrito está vacío")

    pedido = Pedido.objects.create(
        carrito=carrito,
        email=email,
        telefono=telefono
    )

    for item in carrito.items.all():
        ItemPedido.objects.create(
            pedido=pedido,
            producto=item.producto,
            nombre_producto=item.producto.nombre,
            precio_unitario=item.producto.precio,
            cantidad=item.cantidad
        )

    carrito.items.all().delete()

    return pedido
