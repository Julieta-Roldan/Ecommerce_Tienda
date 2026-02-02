# panel_admin/management/commands/crear_grupos.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from tienda.models import Producto, Categoria
from pedidos_pagos.models import Pedido

class Command(BaseCommand):
    help = 'Crea los grupos de permisos iniciales para el sistema'
    
    def handle(self, *args, **kwargs):
        self.stdout.write("Creando grupos de permisos...")
        
        # 1. Grupo: Administradores (acceso total)
        admin_group, created = Group.objects.get_or_create(name='Administradores')
        if created:
            # Dar todos los permisos
            all_perms = Permission.objects.all()
            admin_group.permissions.set(all_perms)
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Administradores" creado con todos los permisos'))
        else:
            self.stdout.write(self.style.WARNING('• Grupo "Administradores" ya existe'))
        
        # 2. Grupo: Empleados (permisos limitados)
        empleado_group, created = Group.objects.get_or_create(name='Empleados')
        if created:
            # Permisos para productos
            content_type_producto = ContentType.objects.get_for_model(Producto)
            permisos_producto = Permission.objects.filter(
                content_type=content_type_producto,
                codename__in=['add_producto', 'change_producto', 'delete_producto', 'view_producto']
            )
            
            # Permisos para categorías
            content_type_categoria = ContentType.objects.get_for_model(Categoria)
            permisos_categoria = Permission.objects.filter(
                content_type=content_type_categoria,
                codename__in=['add_categoria', 'change_categoria', 'delete_categoria', 'view_categoria']
            )
            
            # Permisos para pedidos (solo ver y cambiar)
            content_type_pedido = ContentType.objects.get_for_model(Pedido)
            permisos_pedido = Permission.objects.filter(
                content_type=content_type_pedido,
                codename__in=['change_pedido', 'view_pedido']
            )
            
            # Permisos para el panel admin (vistas específicas)
            content_type_user = ContentType.objects.get(app_label='auth', model='user')
            permisos_user_view = Permission.objects.filter(
                content_type=content_type_user,
                codename='view_user'
            )
            
            # Combinar todos los permisos
            todos_permisos = list(permisos_producto) + list(permisos_categoria) + list(permisos_pedido) + list(permisos_user_view)
            empleado_group.permissions.set(todos_permisos)
            
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Empleados" creado con permisos limitados'))
            self.stdout.write(self.style.SUCCESS('  - Productos: Crear, Editar, Eliminar, Ver'))
            self.stdout.write(self.style.SUCCESS('  - Categorías: Crear, Editar, Eliminar, Ver'))
            self.stdout.write(self.style.SUCCESS('  - Pedidos: Editar, Ver'))
            self.stdout.write(self.style.SUCCESS('  - Usuarios: Ver (solo lista)'))
        else:
            self.stdout.write(self.style.WARNING('• Grupo "Empleados" ya existe'))
        
        # 3. Grupo: Vendedores (solo ver y editar pedidos)
        vendedor_group, created = Group.objects.get_or_create(name='Vendedores')
        if created:
            # Permisos básicos
            permisos_vendedor = Permission.objects.filter(
                codename__in=[
                    'view_pedido', 'change_pedido',  # Pedidos
                    'view_producto', 'view_categoria',  # Solo ver productos y categorías
                ]
            )
            vendedor_group.permissions.set(permisos_vendedor)
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Vendedores" creado (solo pedidos)'))
        else:
            self.stdout.write(self.style.WARNING('• Grupo "Vendedores" ya existe'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Grupos creados exitosamente'))
        self.stdout.write("\nPara asignar usuarios a grupos:")
        self.stdout.write("1. Ve a /panel_admin/usuarios/")
        self.stdout.write("2. Edita un usuario")
        self.stdout.write("3. Selecciona los grupos en 'Permisos y grupos'")