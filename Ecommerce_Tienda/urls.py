"""
URL configuration for Ecommerce_Tienda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views  # Importamos las vistas de la app core


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  # LA RUTA VACÍA DEBE IR AL INDEX
    path('health/', views.health_check),  # Dejamos el test en /health/
     # AGREGAR las urls de las apps (rutas base)
    path('', include('core.urls')),              # home / comprobación básica
    path('tienda/', include('tienda.urls')),    # URLs relacionadas con productos
    path('usuarios/', include('usuarios.urls')),# URLs para gestión interna (no cliente)
    path('carrito/', include('carrito.urls')),  # endpoints del carrito
    path('pedidos/', include('pedidos_pagos.urls')),  # checkout y pagos
    path('pedidos/', include('pedidos_pagos.urls')),
    path('carrito/', include('carrito.urls')),

    
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = [
    
    path('accounts/', include('django.contrib.auth.urls')),
]