# pedidos_pagos/models.py
from django.db import models
from django.db.models import Sum, F
from tienda.models import Producto
from carrito.models import Carrito


class Pedido(models.Model):
    
    @classmethod
    def get_estados(cls):
        """Devuelve las opciones de estado para usar en templates"""
        return cls.ESTADOS

    ESTADOS = [
        ('pendiente', 'Pendiente de pago'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    carrito = models.OneToOneField(
        Carrito,
        on_delete=models.PROTECT,
        related_name='pedido',
        null=True,
        blank=True
    )

    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    
    total_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido #{self.id}"

    @property
    def total(self):
        """Calcula el total sumando los subtotales de los items"""
        return sum(item.subtotal for item in self.items.all())
    
    def get_total_db(self):
        """Versión que funciona en consultas de base de datos"""
        from django.db.models import Sum, F
        total = self.items.aggregate(
            total=Sum(F('precio_unitario') * F('cantidad'))
        )['total'] or 0
        return total


class ItemPedido(models.Model):

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT
    )

    nombre_producto = models.CharField(max_length=200)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Item del pedido'
        verbose_name_plural = 'Items del pedido'

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto}"

    @property
    def subtotal(self):
        """Propiedad Python para calcular subtotal"""
        return self.cantidad * self.precio_unitario
    
    def get_subtotal_db(self):
        """Versión para usar en consultas de base de datos"""
        return self.precio_unitario * self.cantidad


class Pago(models.Model):

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='pagos'
    )

    metodo = models.CharField(
        max_length=50,
        default='mercadopago'
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    referencia_externa = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago #{self.id} - {self.estado}"