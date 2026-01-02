from django.contrib import admin

# Register your models here.
from .models import PerfilEmpleado

@admin.register(PerfilEmpleado)
class PerfilEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('user', 'dni', 'fecha_ingreso', 'activo')
    list_filter = ('activo',)
    search_fields = ('user__username',)
