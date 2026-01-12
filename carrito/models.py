from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from tienda.models import Producto
from django.db import models
from tienda.models import Producto


class Carrito(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito {self.session_key}"


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

def total(self):
    return sum(item.subtotal() for item in self.items.all())

