from django.shortcuts import render
# Create your views here.
# core/views.py  (AGREGAR esta función)
from django.http import HttpResponse



def health_check(request):
    """
    Vista simple para verificar que el backend responde.
    Devuelve texto plano, sin renderizar plantillas.
    """
    return HttpResponse("Ecommerce_Tienda Backend funcionando — core.health_check")

from tienda.models import Producto

# def index(request):
#     # Esto busca tus productos en la base de datos
#     productos_db = Producto.objects.all()[:4] 
    
#     # Esto se los manda al HTML con el nombre 'productos'
#     return render(request, 'core/index.html', {'productos': productos_db})
# core/views.py - FUNCIÓN INDEX MODIFICADA
from tienda.models import Producto, Categoria  # AGREGAR Categoria aquí

def index(request):
    # Traemos los productos activos y sus imágenes
    productos_db = Producto.objects.filter(activo=True).prefetch_related('imagenes')[:8] 
    
    # Les agregamos el cálculo de la cuota a cada uno antes de mandarlos al HTML
    for p in productos_db:
        p.cuota = p.precio / 3
    
    # TRAEMOS LAS CATEGORÍAS ACTIVAS CON IMAGEN DE FONDO
    categorias_db = Categoria.objects.filter(activo=True).exclude(imagen_fondo='').order_by('nombre')[:4]
    
    return render(request, 'core/index.html', {
        'productos': productos_db,
        'categorias': categorias_db  # NUEVO: pasamos categorías al template
    })
#yo

def ubicacion(request):
    return render(request, 'core/ubicacion.html')

def favoritos(request):
    # Aquí simulamos una lista vacía para que no de error
    return render(request, 'core/favoritos.html', {'favoritos': []})

def carrito(request):
    # Cambiamos la ruta para que coincida con tu carpeta 'carrito'
    return render(request, 'carrito/carrito.html', {'items': items, 'total': total})

# AGREGAR AL FINAL de core/views.py
def todas_categorias(request):
    # Traemos TODAS las categorías activas
    categorias_db = Categoria.objects.filter(activo=True).order_by('nombre')
    
    return render(request, 'core/todas_categorias.html', {
        'categorias': categorias_db
    })