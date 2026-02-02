# panel_admin/context_processors.py

def panel_context(request):
    """Context processor para el panel admin"""
    context = {}
    
    if request.user.is_authenticated:
        # Obtener nombres de grupos del usuario
        user_groups = list(request.user.groups.values_list('name', flat=True))
        context['user_groups'] = user_groups
        
        # Contar usuarios inactivos (solo para superuser)
        if request.user.is_superuser:
            from django.contrib.auth.models import User
            usuarios_inactivos = User.objects.filter(is_active=False).count()
            context['usuarios_inactivos'] = usuarios_inactivos
    
    return context