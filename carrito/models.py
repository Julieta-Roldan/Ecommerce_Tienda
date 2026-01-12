from django.db import models
from tienda.models import Producto
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.db import models
from tienda.models import Producto

class Carrito(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito {self.session_key}"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        related_name='items',
        on_delete=models.CASCADE
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"





def agregar_al_carrito(request, producto_id):
    if not request.session.session_key:
        request.session.create()

    carrito, _ = Carrito.objects.get_or_create(
        session_key=request.session.session_key
    )

    producto = get_object_or_404(Producto, id=producto_id)

    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )

    if not creado:
        item.cantidad += 1
        item.save()

    return JsonResponse({
        "mensaje": "Producto agregado al carrito",
        "cantidad": item.cantidad
    })


def ver_carrito(request):
    carrito = None
    items = []

    if request.session.session_key:
        carrito = Carrito.objects.filter(
            session_key=request.session.session_key
        ).first()

        if carrito:
            items = carrito.items.select_related("producto")

    return render(request, "carrito/carrito.html", {
        "carrito": carrito,
        "items": items
    })
