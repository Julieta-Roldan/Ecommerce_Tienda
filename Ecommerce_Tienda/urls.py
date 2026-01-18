from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views  # vistas de la app core


urlpatterns = [
    # ADMIN
    path('admin/', admin.site.urls),

    # HOME PRINCIPAL
    path('', views.index, name='index'),        # página principal (index en core)
    path('health/', views.health_check),        # test / salud

    # AUTH (login / logout / password reset)
    path('accounts/', include('django.contrib.auth.urls')),

    # APPS
    path('tienda/', include('tienda.urls')),            # catálogo / productos
    path('', include('core.urls')),              # home / comprobación básica
    path('carrito/', include('carrito.urls')),          # carrito
    path('pedidos/', include('pedidos_pagos.urls')),    # checkout / pagos
    path('usuarios/', include('usuarios.urls')),        # gestión interna
]

# ARCHIVOS MEDIA


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
