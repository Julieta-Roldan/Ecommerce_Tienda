from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
import json
from .models import PerfilEmpleado


# -----------------------------------------------------------
# LISTAR EMPLEADOS
# -----------------------------------------------------------
def lista_empleados(request):
    empleados = PerfilEmpleado.objects.select_related('user').all()

    data = []
    for emp in empleados:
        data.append({
            "id": emp.id,
            "usuario": emp.user.username,
            "nombre": emp.user.first_name,
            "apellido": emp.user.last_name,
            "dni": emp.dni,
            "fecha_ingreso": emp.fecha_ingreso,
            "activo": emp.activo,
        })

    return JsonResponse({"empleados": data})


# -----------------------------------------------------------
# CREAR EMPLEADO
# -----------------------------------------------------------
@csrf_exempt
def crear_empleado(request):
    if request.method != "POST":
        return JsonResponse({"error": "Solo POST permitido"}, status=400)

    try:
        body = json.loads(request.body)

        username = body.get("username")
        password = body.get("password")
        first_name = body.get("first_name", "")
        last_name = body.get("last_name", "")
        dni = body.get("dni")
        fecha_ingreso = body.get("fecha_ingreso")

        if not username or not password:
            return JsonResponse({"error": "username y password son obligatorios"}, status=400)

        # Crear usuario base
        usuario = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Crear perfil
        perfil = PerfilEmpleado.objects.create(
            user=usuario,
            dni=dni,
            fecha_ingreso=fecha_ingreso,
        )

        return JsonResponse({
            "mensaje": "Empleado creado correctamente",
            "id": perfil.id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# -----------------------------------------------------------
# DETALLE DE EMPLEADO
# -----------------------------------------------------------
def detalle_empleado(request, id):
    empleado = get_object_or_404(PerfilEmpleado, id=id)

    data = {
        "id": empleado.id,
        "usuario": empleado.user.username,
        "nombre": empleado.user.first_name,
        "apellido": empleado.user.last_name,
        "dni": empleado.dni,
        "fecha_ingreso": empleado.fecha_ingreso,
        "activo": empleado.activo,
    }

    return JsonResponse(data)


# -----------------------------------------------------------
# EDITAR EMPLEADO
# -----------------------------------------------------------
@csrf_exempt
def editar_empleado(request, id):
    if request.method != "PUT":
        return JsonResponse({"error": "Solo PUT permitido"}, status=400)

    empleado = get_object_or_404(PerfilEmpleado, id=id)
    user = empleado.user

    body = json.loads(request.body)

    user.first_name = body.get("first_name", user.first_name)
    user.last_name = body.get("last_name", user.last_name)

    empleado.dni = body.get("dni", empleado.dni)
    empleado.fecha_ingreso = body.get("fecha_ingreso", empleado.fecha_ingreso)
    empleado.activo = body.get("activo", empleado.activo)

    user.save()
    empleado.save()

    return JsonResponse({"mensaje": "Empleado actualizado correctamente"})


# -----------------------------------------------------------
# MI PERFIL (DEL USUARIO LOGUEADO)
# -----------------------------------------------------------
@login_required
def mi_perfil(request):
    perfil = get_object_or_404(PerfilEmpleado, user=request.user)

    data = {
        "usuario": request.user.username,
        "nombre": request.user.first_name,
        "apellido": request.user.last_name,
        "dni": perfil.dni,
        "fecha_ingreso": perfil.fecha_ingreso,
        "activo": perfil.activo,
    }

    return JsonResponse(data)
