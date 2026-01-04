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

def index(request):
    return render(request, 'core/index.html')

#yo

def ubicacion(request):
    return render(request, 'core/ubicacion.html')

def favoritos(request):
    # Aquí simulamos una lista vacía para que no de error
    return render(request, 'core/favoritos.html', {'favoritos': []})

def carrito(request):
    # Cambiamos la ruta para que coincida con tu carpeta 'carrito'
    return render(request, 'carrito/carrito.html', {'items': [], 'total': 0})