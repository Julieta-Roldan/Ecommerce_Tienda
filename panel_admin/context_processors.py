# panel_admin/context_processors.py
def panel_context(request):
    """Context processor para el panel admin"""
    context = {}
    
    if request.user.is_authenticated:
        # Obtener los grupos del usuario
        user_groups = list(request.user.groups.values_list('name', flat=True))
        
        context.update({
            'user_groups': user_groups,
            'es_superusuario': request.user.is_superuser,
            'es_staff': request.user.is_staff,
            'puede_ver_estadisticas': request.user.is_superuser or 'Administradores' in user_groups,
            'puede_ver_usuarios': request.user.is_superuser or 'Administradores' in user_groups,
            'puede_ver_productos': request.user.is_superuser or 'Administradores' in user_groups or 'Empleados' in user_groups,
            'puede_ver_categorias': request.user.is_superuser or 'Administradores' in user_groups or 'Empleados' in user_groups,
            'puede_ver_pedidos': request.user.is_superuser or 'Administradores' in user_groups or 'Empleados' in user_groups or 'Vendedores' in user_groups,
        })
    else:
        context.update({
            'user_groups': [],
            'es_superusuario': False,
            'es_staff': False,
            'puede_ver_estadisticas': False,
            'puede_ver_usuarios': False,
            'puede_ver_productos': False,
            'puede_ver_categorias': False,
            'puede_ver_pedidos': False,
        })
    
    return context