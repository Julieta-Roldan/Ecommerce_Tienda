from .models import Pedido, ItemPedido
from carrito.models import ItemCarrito


def crear_pedido_desde_carrito(carrito, email=None, telefono=None):
    """
    Crea un Pedido a partir de un Carrito existente.
    Copia los productos como snapshot.
    """

    # 1. Crear el pedido
    pedido = Pedido.objects.create(
        carrito=carrito,
        email=email,
        telefono=telefono,
    )

    # 2. Copiar los items del carrito al pedido
    items_carrito = ItemCarrito.objects.filter(carrito=carrito)

    for item in items_carrito:
        ItemPedido.objects.create(
            pedido=pedido,
            producto=item.producto,
            nombre_producto=item.producto.nombre,
            precio_unitario=item.producto.precio,
            cantidad=item.cantidad,
        )

    return pedido
