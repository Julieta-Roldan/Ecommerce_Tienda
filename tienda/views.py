from django.shortcuts import render
# Create your views here.
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
#from .models import Producto
import json
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Producto, Categoria, Favorito
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect  
from pedidos_pagos.models import Pedido, ItemPedido
from django.db import transaction
from carrito.models import Carrito, ItemCarrito


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



# Busca tu función catalogo y reemplazala por esta:
# def catalogo(request, nombre_categoria=None):
#     productos = Producto.objects.filter(activo=True)
    
#     if nombre_categoria:
#         # Filtramos por el nombre de la categoría (usamos __iexact para ignorar mayúsculas)
#         productos = productos.filter(categoria__nombre__iexact=nombre_categoria)
    
#     return render(request, 'tienda/catalogo.html', {
#         'productos': productos,
#         'categoria_actual': nombre_categoria
#     })

# def producto_detalle(request, id):
#     producto = get_object_or_404(Producto, id=id)
#     return render(request, 'tienda/producto.html', {'producto': producto})

# Agregamos 'nombre_categoria=None' para que sea opcional
def catalogo(request, nombre_categoria=None): 
    # 1. Traemos todos los productos inicialmente
    productos = Producto.objects.all()

    # 2. Si entramos por una categoría (ej: Pantalones), filtramos
    if nombre_categoria:
        productos = productos.filter(categoria__nombre=nombre_categoria)

    # 3. Mantenemos la lógica de ordenado que ya tenías
    ordenar_por = request.GET.get('orden')
    if ordenar_por == 'menor':
        productos = productos.order_by('precio')
    elif ordenar_por == 'mayor':
        productos = productos.order_by('-precio')
    elif ordenar_por == 'relevantes':
        productos = productos.order_by('-id')

    return render(request, 'tienda/catalogo.html', {
        'productos': productos,
        'categoria_actual': nombre_categoria # Esto te sirve para poner un título dinámico
    })

def producto_detalle(request, id):
    producto = get_object_or_404(
        Producto.objects.prefetch_related('imagenes', 'talles', 'colores'), 
        id=id
    )
    
    # Calculamos el valor de la cuota aquí en Python
    cuota = producto.precio / 3
    
    relacionados = Producto.objects.filter(
        categoria=producto.categoria, 
        activo=True
    ).exclude(id=producto.id)[:4]
    
    return render(request, 'tienda/producto.html', {
        'producto': producto,
        'relacionados': relacionados,
        'cuota': cuota  # Mandamos el valor de la cuota al HTML
    })

def buscar_productos(request):
    query = request.GET.get('q', '')
    if query:
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | 
            Q(categoria__nombre__icontains=query),
            activo=True
        ).prefetch_related('imagenes').distinct() # Agregamos prefetch_related
    else:
        productos = Producto.objects.none()

    return render(request, 'tienda/busqueda.html', {
        'query': query,
        'productos': productos
    })
    
#yo

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
#from .models import Favorito

@login_required # Solo usuarios logueados pueden guardar favoritos
def toggle_favorito(request, id):
    if request.method == "POST":
        producto = get_object_or_404(Producto, id=id)
        favorito, created = Favorito.objects.get_or_create(usuario=request.user, producto=producto)
        
        if not created:
            favorito.delete()
            status = "removed"
        else:
            status = "added"
            
        return JsonResponse({"status": status})
    
    
#lo agrege yo para que lo del admin categoria nueva aparezca en el html todas las categorias

def lista_categorias(request):
    # Ahora que Categoria está en el import de arriba, no va a dar error
    categorias = Categoria.objects.filter(activo=True)
    return render(request, 'tienda/todas_categorias.html', {'categorias': categorias})

# tienda/views.py

def comprar_ahora(request, id):
    """
    Compra rápida: Prepara el carrito con 1 solo producto 
    y redirige al formulario de contacto (Checkout).
    """
    try:
        # 1. Obtenemos el producto (que esté activo y con stock)
        producto = get_object_or_404(Producto, id=id, activo=True, stock__gt=0)
        
        # 2. Aseguramos que el usuario tenga una sesión activa
        if not request.session.session_key:
            request.session.create()
        
        # 3. Obtenemos o creamos el carrito vinculado a la sesión
        carrito, created = Carrito.objects.get_or_create(
            session_key=request.session.session_key
        )
        
        # 4. LIMPIEZA: Borramos lo que hubiera antes para que sea "Compra Única"
        carrito.items.all().delete()
        
        # 5. Agregamos el producto seleccionado
        ItemCarrito.objects.create(
            carrito=carrito,
            producto=producto,
            cantidad=1
        )
        
        # 6. REDIRECCIÓN: En lugar de crear el pedido aquí, 
        # lo mandamos a que ponga su Mail y Teléfono
        return redirect('checkout') # Asegúrate que este nombre coincida con tu urls.py
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Hubo un problema con la compra rápida: {str(e)}")
        return redirect('producto_detalle', id=id)