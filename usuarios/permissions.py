from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from tienda.models import Producto, Categoria
from usuarios.models import PerfilEmpleado
from pedidos_pagos.models import Pedido

def crear_roles():
    # --- GRUPO DUEÑO ---
    dueno, _ = Group.objects.get_or_create(name='Dueño')

    # Permisos de productos
    permisos_producto = Permission.objects.filter(
        content_type=ContentType.objects.get_for_model(Producto)
    )
    permisos_categoria = Permission.objects.filter(
        content_type=ContentType.objects.get_for_model(Categoria)
    )
    permisos_pedido = Permission.objects.filter(
        content_type=ContentType.objects.get_for_model(Pedido)
    )
    permisos_empleados = Permission.objects.filter(
        content_type=ContentType.objects.get_for_model(PerfilEmpleado)
    )

    # Asignar todos
    dueno.permissions.set(
        list(permisos_producto) +
        list(permisos_categoria) +
        list(permisos_pedido) +
        list(permisos_empleados)
    )

    # --- GRUPO EMPLEADO ---
    empleado, _ = Group.objects.get_or_create(name='Empleado')

    # Solo CRUD productos
    empleado.permissions.set(
        list(permisos_producto) +
        list(permisos_categoria)
    )
