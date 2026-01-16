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

def index(request):
    # Traemos los productos activos y sus imágenes
    productos_db = Producto.objects.filter(activo=True).prefetch_related('imagenes')[:8] 
    
    # Les agregamos el cálculo de la cuota a cada uno antes de mandarlos al HTML
    for p in productos_db:
        p.cuota = p.precio / 3

    return render(request, 'core/index.html', {'productos': productos_db})

#yo

def ubicacion(request):
    return render(request, 'core/ubicacion.html')

def favoritos(request):
    # Aquí simulamos una lista vacía para que no de error
    return render(request, 'core/favoritos.html', {'favoritos': []})

def carrito(request):
    # Cambiamos la ruta para que coincida con tu carpeta 'carrito'
    return render(request, 'carrito/carrito.html', {'items': items, 'total': total})

