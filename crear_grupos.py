import os
import django
import sys

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ecommerce_Tienda.settings')
django.setup()

from django.contrib.auth.models import Group

print("=== CREANDO GRUPOS BÁSICOS DEL SISTEMA ===")

grupos_basicos = ['Administradores', 'Empleados', 'Vendedores']

for nombre_grupo in grupos_basicos:
    grupo, creado = Group.objects.get_or_create(name=nombre_grupo)
    if creado:
        print(f"✅ Grupo creado: {nombre_grupo} (ID: {grupo.id})")
    else:
        print(f"✅ Grupo ya existe: {nombre_grupo} (ID: {grupo.id})")

print("\n=== GRUPOS EXISTENTES ===")
for grupo in Group.objects.all():
    print(f"ID: {grupo.id} | Nombre: {grupo.name}")