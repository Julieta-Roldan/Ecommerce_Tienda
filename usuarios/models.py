from django.db import models

# Create your models here.
from django.contrib.auth.models import User

ROLES = (
    ('empleado', 'Empleado'),
    ('admin', 'Administrador'),
)

class PerfilEmpleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    dni = models.CharField(max_length=20, blank=True, null=True)
    fecha_ingreso = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    

rol = models.CharField(max_length=20, choices= ROLES, default='empleado')

class Meta:
        verbose_name = 'Perfil de empleado'
        verbose_name_plural = 'Perfiles de empleados'

def __str__(self):
        return f"{self.user.username}"