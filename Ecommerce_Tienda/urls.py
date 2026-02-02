from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views  # vistas de la app core

urlpatterns = [
    # ADMIN
   path('panel_admin/', include('panel_admin.urls', namespace='panel_admin')),
   path('admin/', admin.site.urls), 
    # HOME PRINCIPAL
    path('', views.index, name='index'),
    path('health/', views.health_check),

    # AUTH
    path('accounts/', include('django.contrib.auth.urls')),

    # APPS
    path('tienda/', include('tienda.urls')),
    path('', include('core.urls')),
    path('carrito/', include('carrito.urls')),
    path('pedidos/', include('pedidos_pagos.urls')),
    path('usuarios/', include('usuarios.urls')),
]

# ARCHIVOS MEDIA
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
