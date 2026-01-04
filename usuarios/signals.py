from django.contrib.auth.models import User, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

from .models import PerfilEmpleado


@receiver(post_save, sender=User)
def crear_perfil_empleado(sender, instance, created, **kwargs):
    if created:
        PerfilEmpleado.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_empleado(sender, instance, **kwargs):
    if hasattr(instance, 'perfilempleado'):
        instance.perfilempleado.save()


def crear_roles(sender=None, **kwargs):

    # GRUPO DUEÑO
    duenio_group, _ = Group.objects.get_or_create(name='Dueño')
    duenio_group.permissions.set(Permission.objects.all())

    # GRUPO EMPLEADO
    empleado_group, _ = Group.objects.get_or_create(name='Empleado')

    permisos_empleado = []

    tienda_models = apps.get_app_config('tienda').get_models()

    for model in tienda_models:
        perms = Permission.objects.filter(
            content_type__model=model.__name__.lower()
        )
        permisos_empleado.extend(perms)

    empleado_group.permissions.set(permisos_empleado)

    # Asignar Dueño a superusuarios
    for user in User.objects.filter(is_superuser=True):
        user.groups.add(duenio_group)
