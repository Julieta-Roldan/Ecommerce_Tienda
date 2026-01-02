from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import PerfilEmpleado
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.dispatch import receiver
from django.apps import apps



@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilEmpleado.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil(sender, instance, **kwargs):
    instance.perfilempleado.save()


@receiver(post_migrate)
def create_roles(sender, **kwargs):
    if sender.name != 'usuarios':
        return

    # Crear o obtener grupos
    duenio_group, _ = Group.objects.get_or_create(name='Dueño')
    empleado_group, _ = Group.objects.get_or_create(name='Empleado')

    # Permisos completos para el Dueño
    all_permissions = Permission.objects.all()
    duenio_group.permissions.set(all_permissions)

    # Permisos limitados para Empleado
    tienda_models = apps.get_app_config('tienda').get_models()
    permisos_empleado = []

    for model in tienda_models:
        perms = Permission.objects.filter(content_type__model=model.__name__.lower())
        permisos_empleado.extend(perms)

    empleado_group.permissions.set(permisos_empleado)


@receiver(post_migrate)
def assign_superuser_role(sender, **kwargs):
    if sender.name != 'usuarios':
        return

    try:
        superusers = User.objects.filter(is_superuser=True)
        duenio_group = Group.objects.get(name='Dueño')
        for su in superusers:
            su.groups.add(duenio_group)
    except:
        pass
