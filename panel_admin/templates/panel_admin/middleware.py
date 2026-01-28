# panel_admin/middleware.py
from pedidos_pagos.models import Pedido

class PedidosPendientesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo para usuarios staff
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
            request.session['pedidos_pendientes'] = pedidos_pendientes
        
        response = self.get_response(request)
        return response