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

