from django.shortcuts import render
# Create your views here.
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
from .models import Producto
import json
from django.shortcuts import get_object_or_404



# LISTAR PRODUCTOS
@login_required
def listar_productos(request):
    productos = Producto.objects.all().values(
        'id', 'nombre', 'descripcion', 'precio', 'stock', 'categoria__nombre'
    )
    return JsonResponse(list(productos), safe=False)

# OBTENER UN PRODUCTO
@login_required
def obtener_producto(request, producto_id):
    try:
        p = Producto.objects.get(id=producto_id)
        data = {
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio': float(p.precio),
            'stock': p.stock,
            'categoria': p.categoria.nombre,
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

# CREAR PRODUCTO
@csrf_exempt
@login_required
@permission_required('tienda.add_producto', raise_exception=True)
def crear_producto(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        p = Producto.objects.create(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            precio=data['precio'],
            stock=data['stock'],
            categoria_id=data['categoria_id']
        )
        return JsonResponse({'mensaje': 'Producto creado', 'id': p.id})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# ACTUALIZAR PRODUCTO
@csrf_exempt
@login_required
@permission_required('tienda.change_producto', raise_exception=True)
def actualizar_producto(request, producto_id):
    try:
        p = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    if request.method == 'PUT':
        data = json.loads(request.body)
        p.nombre = data.get('nombre', p.nombre)
        p.descripcion = data.get('descripcion', p.descripcion)
        p.precio = data.get('precio', p.precio)
        p.stock = data.get('stock', p.stock)
        p.categoria_id = data.get('categoria_id', p.categoria_id)
        p.save()
        return JsonResponse({'mensaje': 'Producto actualizado'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# ELIMINAR PRODUCTO
@csrf_exempt
@login_required
@permission_required('tienda.delete_producto', raise_exception=True)
def eliminar_producto(request, producto_id):
    try:
        p = Producto.objects.get(id=producto_id)
        p.delete()
        return JsonResponse({'mensaje': 'Producto eliminado'})
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)



def catalogo(request):
    productos = Producto.objects.all()
    return render(request, 'tienda/catalogo.html', {'productos': productos})



def producto_detalle(request, id):
    producto = get_object_or_404(Producto, id=id)
    return render(request, 'tienda/producto.html', {'producto': producto})
