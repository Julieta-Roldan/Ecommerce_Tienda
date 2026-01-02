from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from tienda.models import Producto


class Pedido(models.Model):

    ESTADOS = [
        ('pendiente', 'Pendiente de pago'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    cliente_email = models.EmailField(blank=True, null=True)
    cliente_telefono = models.CharField(max_length=30, blank=True, null=True)
    
    # AGREGAR estos campos al modelo Pedido

    email_cliente = models.EmailField(blank=True, null=True)
    telefono_cliente = models.CharField(max_length=20, blank=True, null=True)


    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    def __str__(self):
        return f"Pedido #{self.id}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
