# panel_admin/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, DecimalField, ExpressionWrapper
from django.utils import timezone
from datetime import timedelta
from tienda.models import Producto, Categoria, ImagenProducto
from pedidos_pagos.models import Pedido, ItemPedido
from carrito.models import Carrito
from django.core.paginator import Paginator
from django.http import JsonResponse
from tienda.forms import ProductoForm
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib.auth.models import Group, Permission
from tienda.models import Talle, Color 
from pedidos_pagos.models import Pedido

# ==================== DECORADORES PERSONALIZADOS ====================

# ==================== DECORADORES PERSONALIZADOS ====================

def requiere_permiso(permiso_codename):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(permiso_codename):
                if request.user.is_authenticated:
                    raise PermissionDenied
                else:
                    return redirect('panel_admin:login')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def es_staff(user):
    if user.is_superuser or user.is_staff:
        return True
    grupos_con_acceso = ['Administradores', 'Empleados', 'Vendedores']
    return user.groups.filter(name__in=grupos_con_acceso).exists()

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            if request.user.is_authenticated:
                messages.error(request, 'No tienes permisos de administrador')
                return redirect('panel_admin:dashboard')
            else:
                return redirect('panel_admin:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def puede_ver_dashboard(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Administradores', 'Empleados', 'Vendedores']).exists()

def puede_gestionar_usuarios(user):
    return user.is_superuser or user.groups.filter(name='Administradores').exists()

# ==================== DECORADORES ESPECÍFICOS POR SECCIÓN ====================

def requiere_ver_dashboard(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name__in=['Administradores', 'Empleados', 'Vendedores']).exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'No tienes permisos para acceder al panel')
            return redirect('/')
    return _wrapped_view

def requiere_ver_productos(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name__in=['Administradores', 'Empleados']).exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'No tienes permisos para acceder a la sección de Productos')
            return redirect('panel_admin:dashboard')
    return _wrapped_view

def requiere_ver_categorias(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name__in=['Administradores', 'Empleados']).exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'No tienes permisos para acceder a la sección de Categorías')
            return redirect('panel_admin:dashboard')
    return _wrapped_view

def requiere_ver_pedidos(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name__in=['Administradores', 'Empleados', 'Vendedores']).exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'No tienes permisos para acceder a la sección de Pedidos')
            return redirect('panel_admin:dashboard')
    return _wrapped_view

# NUEVO: Decorador específico para estadísticas (solo superusuarios y administradores)
def requiere_ver_estadisticas(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name='Administradores').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'No tienes permisos para acceder a Estadísticas')
            return redirect('panel_admin:dashboard')
    return _wrapped_view

# NUEVO: Decorador específico para usuarios (solo superusuarios y administradores)
def requiere_ver_usuarios(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name='Administradores').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'No tienes permisos para acceder a la sección de Usuarios')
            return redirect('panel_admin:dashboard')
    return _wrapped_view

# ==================== AUTENTICACIÓN ====================
def login_panel(request):
    # Si ya está autenticado y es staff, redirigir al dashboard
    if request.user.is_authenticated:
        if es_staff(request.user):
            return redirect('panel_admin:dashboard')
        else:
            messages.error(request, 'No tienes permisos para acceder al panel')
            return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if es_staff(user):
                login(request, user)
                messages.success(request, f'Bienvenido, {user.username}!')
                # Redirigir según el tipo de usuario
                return redirect('panel_admin:dashboard')
            else:
                messages.error(request, 'Tu cuenta no tiene permisos para acceder al panel administrativo')
        else:
            messages.error(request, 'Credenciales inválidas')
    
    return render(request, 'panel_admin/login.html')



def logout_panel(request):
    """Cerrar sesión del panel administrativo"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Sesión cerrada correctamente. Hasta pronto, {username}!')
    else:
        messages.info(request, 'No hay una sesión activa')
    
    return redirect('panel_admin:login')

# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    # Verificar permisos directamente en la vista
    if not es_staff(request.user):
        messages.error(request, 'No tienes permisos para acceder al panel')
        return redirect('/')
    
    user_groups = list(request.user.groups.values_list('name', flat=True))
    
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_pagados = Pedido.objects.filter(estado='pagado').count()
    
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    ventas_mes = ItemPedido.objects.filter(
        pedido__estado__in=['pagado', 'enviado', 'entregado'],
        pedido__fecha_creacion__gte=inicio_mes
    ).aggregate(
        total=Sum(F('precio_unitario') * F('cantidad'), output_field=DecimalField(max_digits=12, decimal_places=2))
    )['total'] or 0
    
    pedidos_recientes = Pedido.objects.order_by('-fecha_creacion')[:5]
    productos_stock_bajo = Producto.objects.filter(stock__lt=10, stock__gt=0)[:5]
    productos_sin_stock = Producto.objects.filter(stock=0)[:5]
    usuarios_inactivos = User.objects.filter(is_active=False).count()
    
    context = {
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_pagados': pedidos_pagados,
        'ventas_mes': ventas_mes,
        'pedidos_recientes': pedidos_recientes,
        'productos_stock_bajo': productos_stock_bajo,
        'productos_sin_stock': productos_sin_stock,
        'usuarios_inactivos': usuarios_inactivos,
        'user_groups': user_groups,
    }
    
    return render(request, 'panel_admin/dashboard.html', context)
# ==================== PRODUCTOS ====================
@login_required
@user_passes_test(es_staff)
@requiere_ver_productos
def productos_lista(request):
    productos = Producto.objects.all().order_by('-creado')
    
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    estado = request.GET.get('estado')
    if estado == 'activos':
        productos = productos.filter(activo=True)
    elif estado == 'inactivos':
        productos = productos.filter(activo=False)
    
    busqueda = request.GET.get('q')
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda)
        )
    
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'filtro_categoria': categoria_id,
        'filtro_estado': estado,
        'busqueda': busqueda,
    }
    
    return render(request, 'panel_admin/productos/lista.html', context)

@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def producto_nuevo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria_id = request.POST.get('categoria')
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        descripcion = request.POST.get('descripcion', '')
        activo = request.POST.get('activo') == 'on'
        
        errores = []
        if not nombre:
            errores.append('El nombre es requerido')
        if not categoria_id:
            errores.append('La categoría es requerida')
        if not precio or float(precio) <= 0:
            errores.append('El precio debe ser mayor a 0')
        if not stock or int(stock) < 0:
            errores.append('El stock no puede ser negativo')
        
        if errores:
            for error in errores:
                messages.error(request, error)
        else:
            try:
                categoria = Categoria.objects.get(id=categoria_id)
                producto = Producto.objects.create(
                    nombre=nombre,
                    categoria=categoria,
                    precio=precio,
                    stock=stock,
                    descripcion=descripcion,
                    activo=activo
                )
                
                talles_ids = request.POST.getlist('talles')
                if talles_ids:
                    talles = Talle.objects.filter(id__in=talles_ids)
                    producto.talles.set(talles)
                
                colores_ids = request.POST.getlist('colores')
                if colores_ids:
                    colores = Color.objects.filter(id__in=colores_ids)
                    producto.colores.set(colores)
                
                if 'imagen_principal' in request.FILES:
                    imagen = request.FILES['imagen_principal']
                    ImagenProducto.objects.create(
                        producto=producto, 
                        imagen=imagen,
                        es_principal=True
                    )
                
                messages.success(request, f'Producto "{producto.nombre}" creado correctamente')
                return redirect('panel_admin:productos')
                
            except Categoria.DoesNotExist:
                messages.error(request, 'Categoría no válida')
            except Exception as e:
                messages.error(request, f'Error al crear producto: {str(e)}')
    
    categorias = Categoria.objects.filter(activo=True)
    talles = Talle.objects.all()
    colores = Color.objects.all()
    
    return render(request, 'panel_admin/productos/form.html', {
        'categorias': categorias,
        'talles': talles,
        'colores': colores,
        'titulo': 'Nuevo Producto',
        'accion': 'Crear'
    })

@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def producto_editar(request, id):
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria_id = request.POST.get('categoria')
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        descripcion = request.POST.get('descripcion', '')
        activo = request.POST.get('activo') == 'on'
        
        errores = []
        if not nombre:
            errores.append('El nombre es requerido')
        if not categoria_id:
            errores.append('La categoría es requerida')
        if not precio or float(precio) <= 0:
            errores.append('El precio debe ser mayor a 0')
        if not stock or int(stock) < 0:
            errores.append('El stock no puede ser negativo')
        
        if errores:
            for error in errores:
                messages.error(request, error)
        else:
            try:
                categoria = Categoria.objects.get(id=categoria_id)
                
                producto.nombre = nombre
                producto.categoria = categoria
                producto.precio = precio
                producto.stock = stock
                producto.descripcion = descripcion
                producto.activo = activo
                producto.save()
                
                talles_ids = request.POST.getlist('talles')
                if talles_ids:
                    talles = Talle.objects.filter(id__in=talles_ids)
                    producto.talles.set(talles)
                else:
                    producto.talles.clear()
                
                colores_ids = request.POST.getlist('colores')
                if colores_ids:
                    colores = Color.objects.filter(id__in=colores_ids)
                    producto.colores.set(colores)
                else:
                    producto.colores.clear()
                
                if 'imagen_principal' in request.FILES:
                    producto.imagenes.filter(es_principal=True).delete()
                    imagen = request.FILES['imagen_principal']
                    ImagenProducto.objects.create(
                        producto=producto, 
                        imagen=imagen,
                        es_principal=True
                    )
                
                messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente')
                return redirect('panel_admin:productos')
                
            except Categoria.DoesNotExist:
                messages.error(request, 'Categoría no válida')
            except Exception as e:
                messages.error(request, f'Error al actualizar producto: {str(e)}')
    
    categorias = Categoria.objects.filter(activo=True)
    talles = Talle.objects.all()
    colores = Color.objects.all()
    
    return render(request, 'panel_admin/productos/form.html', {
        'producto': producto,
        'categorias': categorias,
        'talles': talles,
        'colores': colores,
        'titulo': f'Editar: {producto.nombre}',
        'accion': 'Actualizar'
    })

@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def producto_eliminar(request, id):
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        producto_nombre = producto.nombre
        categoria_nombre = producto.categoria.nombre
        
        producto.imagenes.all().delete()
        producto.favorito_set.all().delete()
        producto.talles.clear()
        producto.colores.clear()
        producto.delete()
        
        messages.success(request, f'Producto "{producto_nombre}" ELIMINADO PERMANENTEMENTE de la categoría "{categoria_nombre}"')
        return redirect('panel_admin:productos')
    
    return render(request, 'panel_admin/productos/confirmar_eliminar.html', {
        'producto': producto
    })

# ==================== PEDIDOS ====================
@login_required
@user_passes_test(es_staff)
@requiere_ver_pedidos 
def pedidos_lista(request):
    pedidos = Pedido.objects.all().order_by('-fecha_creacion')
    
    estado = request.GET.get('estado')
    if estado:
        pedidos = pedidos.filter(estado=estado)
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        pedidos = pedidos.filter(fecha_creacion__gte=fecha_desde)
    if fecha_hasta:
        pedidos = pedidos.filter(fecha_creacion__lte=fecha_hasta)
    
    paginator = Paginator(pedidos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_pendientes = Pedido.objects.filter(estado='pendiente').count()
    total_pagados = Pedido.objects.filter(estado='pagado').count()
    
    # Obtener estados disponibles
    ESTADOS_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    context = {
        'page_obj': page_obj,
        'total_pendientes': total_pendientes,
        'total_pagados': total_pagados,
        'filtro_estado': estado,
        'filtro_fecha_desde': fecha_desde,
        'filtro_fecha_hasta': fecha_hasta,
        'estados_pedido': ESTADOS_PEDIDO,
    }
    
    return render(request, 'panel_admin/pedidos/lista.html', context)

@login_required
@user_passes_test(es_staff)
@requiere_ver_pedidos 
def pedido_detalle(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    
    total_pedido = pedido.get_total_db()
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Pedido.ESTADOS).keys():
            estado_anterior = pedido.estado
            pedido.estado = nuevo_estado
            pedido.save()
            
            if nuevo_estado == 'entregado' and pedido.carrito:
                pedido.carrito.items.all().delete()
            
            messages.success(request, 
                f'Pedido #{pedido.id} cambiado de "{estado_anterior}" a "{nuevo_estado}"'
            )
        return redirect('panel_admin:pedido_detalle', id=id)
    
    context = {
        'pedido': pedido,
        'items': pedido.items.all(),
        'estados_disponibles': Pedido.ESTADOS,
        'total_pedido': total_pedido,
    }
    
    return render(request, 'panel_admin/pedidos/detalle.html', context)

@login_required
@user_passes_test(es_staff)
@requiere_ver_pedidos 
def cambiar_estado_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in dict(Pedido.ESTADOS).keys():
            estado_anterior = pedido.estado
            pedido.estado = nuevo_estado
            pedido.save()
            
            if nuevo_estado in ['entregado', 'cancelado'] and pedido.carrito:
                pedido.carrito.items.all().delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'nuevo_estado': pedido.estado,
                    'estado_display': pedido.get_estado_display(),
                    'mensaje': f'Pedido #{pedido.id} cambiado a "{pedido.get_estado_display()}"'
                })
            else:
                messages.success(request, 
                    f'Pedido #{pedido.id} cambiado de "{estado_anterior}" a "{nuevo_estado}"'
                )
                return redirect('panel_admin:pedidos')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False, 
            'error': 'Método no permitido o estado inválido'
        }, status=400)
    else:
        messages.error(request, 'Error al cambiar estado del pedido')
        return redirect('panel_admin:pedidos')

# ==================== ESTADÍSTICAS ====================
@login_required
@requiere_ver_estadisticas
def estadisticas(request):
    hoy = timezone.now()
    
    fecha_inicio = hoy - timedelta(days=30)
    
    ventas_por_dia = ItemPedido.objects.filter(
        pedido__fecha_creacion__gte=fecha_inicio,
        pedido__estado__in=['pagado', 'enviado', 'entregado']
    ).annotate(
        subtotal_db=ExpressionWrapper(
            F('precio_unitario') * F('cantidad'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    ).extra(
        select={'fecha': 'DATE(pedidos_pagos_pedido.fecha_creacion)'}
    ).values('fecha').annotate(
        total=Sum('subtotal_db'),
        cantidad_pedidos=Count('pedido', distinct=True)
    ).order_by('fecha')
    
    productos_mas_vendidos = ItemPedido.objects.filter(
        pedido__estado__in=['pagado', 'enviado', 'entregado']
    ).annotate(
        subtotal_db=ExpressionWrapper(
            F('precio_unitario') * F('cantidad'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    ).values(
        'producto__id', 
        'producto__nombre',
        'producto__precio'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum('subtotal_db')
    ).order_by('-total_vendido')[:10]
    
    categorias_populares = Categoria.objects.annotate(
        total_productos=Count('producto'),
        total_vendidos=Count('producto__itempedido')
    ).order_by('-total_vendidos')[:5]
    
    context = {
        'ventas_por_dia': list(ventas_por_dia),
        'productos_mas_vendidos': productos_mas_vendidos,
        'categorias_populares': categorias_populares,
        'hoy': hoy.date(),
        'hace_30_dias': (hoy - timedelta(days=30)).date(),
    }
    
    return render(request, 'panel_admin/estadisticas.html', context)

# ==================== CATEGORÍAS ====================
@login_required
@user_passes_test(es_staff)
@requiere_ver_categorias 
def categorias_lista(request):
    categorias = Categoria.objects.all().order_by('-creado', 'nombre')
    
    busqueda = request.GET.get('q')
    if busqueda:
        categorias = categorias.filter(nombre__icontains=busqueda)
    
    estado = request.GET.get('estado')
    if estado == 'activas':
        categorias = categorias.filter(activo=True)
    elif estado == 'inactivas':
        categorias = categorias.filter(activo=False)
    elif estado == 'con_productos':
        categorias = categorias.annotate(num_productos=Count('producto')).filter(num_productos__gt=0)
    elif estado == 'sin_productos':
        categorias = categorias.annotate(num_productos=Count('producto')).filter(num_productos=0)
    
    categorias_activas = Categoria.objects.filter(activo=True).count()
    categorias_con_productos = Categoria.objects.annotate(
        num_productos=Count('producto')
    ).filter(num_productos__gt=0).count()
    total_productos = Producto.objects.count()
    
    context = {
        'categorias': categorias,
        'busqueda': busqueda,
        'categorias_activas': categorias_activas,
        'categorias_con_productos': categorias_con_productos,
        'total_productos': total_productos,
    }
    
    return render(request, 'panel_admin/categorias/lista.html', context)

@login_required
@user_passes_test(es_staff)
@requiere_ver_categorias 
def categoria_nueva(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        activo = request.POST.get('activo') == 'on'
        
        if nombre:
            categoria = Categoria.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                activo=activo
            )
            
            if 'imagen_fondo' in request.FILES:
                imagen = request.FILES['imagen_fondo']
                categoria.imagen_fondo = imagen
                categoria.save()
            
            messages.success(request, f'Categoría "{categoria.nombre}" creada correctamente')
            return redirect('panel_admin:categorias')
        else:
            messages.error(request, 'El nombre de la categoría es requerido')
    
    return render(request, 'panel_admin/categorias/form.html', {
        'titulo': 'Nueva Categoría',
        'accion': 'Crear'
    })

@login_required
@user_passes_test(es_staff)
@requiere_ver_categorias 
def categoria_editar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        activo = request.POST.get('activo') == 'on'
        
        if nombre:
            categoria.nombre = nombre
            categoria.descripcion = descripcion
            categoria.activo = activo
            
            if 'imagen_fondo' in request.FILES:
                imagen = request.FILES['imagen_fondo']
                categoria.imagen_fondo = imagen
            
            if 'quitar_imagen' in request.POST and request.POST['quitar_imagen'] == 'true':
                categoria.imagen_fondo.delete(save=False)
                categoria.imagen_fondo = None
            
            categoria.save()
            
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada correctamente')
            return redirect('panel_admin:categorias')
        else:
            messages.error(request, 'El nombre de la categoría es requerido')
    
    return render(request, 'panel_admin/categorias/form.html', {
        'titulo': f'Editar: {categoria.nombre}',
        'accion': 'Actualizar',
        'categoria': categoria
    })

@login_required
@user_passes_test(es_staff)
@requiere_ver_categorias 
def categoria_eliminar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        categoria_nombre = categoria.nombre
        accion = request.POST.get('accion')
        
        if accion == 'desactivar':
            categoria.activo = False
            categoria.save()
            messages.success(request, f'Categoría "{categoria_nombre}" desactivada correctamente')
            return redirect('panel_admin:categorias')
        
        elif accion == 'eliminar':
            if categoria.producto_set.exists():
                messages.error(request, 
                    f'No se puede eliminar la categoría "{categoria_nombre}" porque tiene productos asociados. '
                    'Usa la opción "Desactivar" en su lugar.'
                )
                return redirect('panel_admin:categorias')
            
            categoria.delete()
            messages.success(request, f'Categoría "{categoria_nombre}" eliminada correctamente')
            return redirect('panel_admin:categorias')
        
        elif accion == 'mover_y_eliminar':
            nueva_categoria_id = request.POST.get('nueva_categoria')
            if nueva_categoria_id:
                try:
                    nueva_categoria = Categoria.objects.get(id=nueva_categoria_id)
                    productos_afectados = categoria.producto_set.all()
                    for producto in productos_afectados:
                        producto.categoria = nueva_categoria
                        producto.save()
                    
                    categoria.delete()
                    messages.success(request, 
                        f'Categoría "{categoria_nombre}" eliminada. '
                        f'{productos_afectados.count()} productos movidos a "{nueva_categoria.nombre}"'
                    )
                    return redirect('panel_admin:categorias')
                except Categoria.DoesNotExist:
                    messages.error(request, 'Categoría destino no válida')
            else:
                messages.error(request, 'Debes seleccionar una categoría destino')
    
    otras_categorias = Categoria.objects.exclude(id=id).filter(activo=True)
    
    return render(request, 'panel_admin/categorias/confirmar_eliminar.html', {
        'categoria': categoria,
        'otras_categorias': otras_categorias,
    })

# ==================== USUARIOS/EMPLEADOS ====================
@login_required
@requiere_ver_usuarios
def usuarios_lista(request):
    usuarios = User.objects.all().order_by('-date_joined')
    
    tipo = request.GET.get('tipo')
    if tipo == 'staff':
        usuarios = usuarios.filter(is_staff=True)
    elif tipo == 'superusers':
        usuarios = usuarios.filter(is_superuser=True)
    elif tipo == 'activos':
        usuarios = usuarios.filter(is_active=True)
    elif tipo == 'inactivos':
        usuarios = usuarios.filter(is_active=False)
    
    busqueda = request.GET.get('q')
    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda) |
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    paginator = Paginator(usuarios, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    staff_count = User.objects.filter(is_staff=True).count()
    superusers_count = User.objects.filter(is_superuser=True).count()
    active_count = User.objects.filter(is_active=True).count()
    
    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'filtro_tipo': tipo,
        'staff_count': staff_count,
        'superusers_count': superusers_count,
        'active_count': active_count,
        'puede_editar_usuarios': request.user.is_superuser,
    }
    
    return render(request, 'panel_admin/usuarios/lista.html', context)

@login_required
@requiere_ver_usuarios
def usuario_nuevo(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        grupos_ids = request.POST.getlist('groups')
        grupos = Group.objects.filter(id__in=grupos_ids)
        
        permisos_ids = []
        if request.user.is_superuser:
            permisos_ids = request.POST.getlist('user_permissions')
        permisos = Permission.objects.filter(id__in=permisos_ids)
        
        if username and password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe')
            else:
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_staff=is_staff,
                        is_active=is_active
                    )
                    
                    user.groups.set(grupos)
                    
                    if request.user.is_superuser:
                        user.user_permissions.set(permisos)
                    
                    messages.success(request, f'Usuario "{user.username}" creado correctamente')
                    return redirect('panel_admin:usuarios')
                    
                except Exception as e:
                    messages.error(request, f'Error al crear usuario: {str(e)}')
        else:
            messages.error(request, 'Nombre de usuario y contraseña son requeridos')
    
    grupos = Group.objects.all().order_by('name')
    permisos = Permission.objects.all().order_by('name') if request.user.is_superuser else []
    
    return render(request, 'panel_admin/usuarios/form.html', {
        'titulo': 'Nuevo Usuario/Empleado',
        'accion': 'Crear',
        'grupos': grupos,
        'permisos': permisos,
        'es_superuser': request.user.is_superuser,
    })
    
@login_required
@requiere_ver_usuarios
def usuario_editar(request, id):
    usuario = get_object_or_404(User, id=id)
    
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para editar superusuarios')
        return redirect('panel_admin:usuarios')
    
    if not request.user.is_superuser and usuario.groups.filter(name='Administradores').exists():
        messages.error(request, 'No puedes editar a otros administradores')
        return redirect('panel_admin:usuarios')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        grupos_ids = request.POST.getlist('groups')
        grupos = Group.objects.filter(id__in=grupos_ids)
        
        permisos_ids = []
        if request.user.is_superuser:
            permisos_ids = request.POST.getlist('user_permissions')
        permisos = Permission.objects.filter(id__in=permisos_ids)
        
        usuario.email = email
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.is_staff = is_staff
        usuario.is_active = is_active
        
        nueva_password = request.POST.get('password')
        if nueva_password:
            usuario.set_password(nueva_password)
        
        usuario.save()
        
        usuario.groups.set(grupos)
        
        if request.user.is_superuser:
            usuario.user_permissions.set(permisos)
        
        messages.success(request, f'Usuario "{usuario.username}" actualizado correctamente')
        return redirect('panel_admin:usuarios')
    
    grupos = Group.objects.all().order_by('name')
    permisos = Permission.objects.all().order_by('name') if request.user.is_superuser else []
    
    return render(request, 'panel_admin/usuarios/form.html', {
        'titulo': f'Editar: {usuario.username}',
        'accion': 'Actualizar',
        'usuario': usuario,
        'grupos': grupos,
        'permisos': permisos,
        'es_superuser': request.user.is_superuser,
    })

@login_required
@requiere_ver_usuarios
def usuario_eliminar(request, id):
    """Eliminar un usuario"""
    usuario = get_object_or_404(User, id=id)
    
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta')
        return redirect('panel_admin:usuarios')
    
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para eliminar superusuarios')
        return redirect('panel_admin:usuarios')
    
    if not request.user.is_superuser and usuario.groups.filter(name='Administradores').exists():
        messages.error(request, 'No puedes eliminar a otros administradores')
        return redirect('panel_admin:usuarios')
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado correctamente')
        return redirect('panel_admin:usuarios')
    
    context = {
        'usuario': usuario,
    }
    return render(request, 'panel_admin/usuarios/confirmar_eliminar.html', context)


# ==================== TALLES Y COLORES RÁPIDOS ====================

@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def agregar_talle_rapido(request):
    """Agregar talle rápido desde AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        nombre_talle = request.POST.get('nombre')
        
        if nombre_talle:
            try:
                talle, created = Talle.objects.get_or_create(nombre=nombre_talle.strip())
                return JsonResponse({
                    'success': True,
                    'id': talle.id,
                    'nombre': talle.nombre,
                    'created': created
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def agregar_color_rapido(request):
    """Agregar color rápido desde AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        nombre_color = request.POST.get('nombre')
        codigo_hex = request.POST.get('codigo_hex', '#000000')
        
        if nombre_color:
            try:
                color, created = Color.objects.get_or_create(
                    nombre=nombre_color.strip(),
                    defaults={'codigo_hex': codigo_hex}
                )
                return JsonResponse({
                    'success': True,
                    'id': color.id,
                    'nombre': color.nombre,
                    'codigo_hex': color.codigo_hex or '#000000',
                    'created': created
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def eliminar_talle_rapido(request):
    """Eliminar talle desde AJAX (solo si no está en uso)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        talle_id = request.POST.get('id')
        
        try:
            talle = Talle.objects.get(id=talle_id)
            talle_nombre = talle.nombre
            
            # Verificar si el talle está siendo usado por algún producto
            if talle.producto_set.exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'El talle "{talle_nombre}" está siendo usado por {talle.producto_set.count()} productos. No se puede eliminar.'
                })
            
            # Eliminar el talle
            talle.delete()
            return JsonResponse({
                'success': True,
                'message': f'Talle "{talle_nombre}" eliminado correctamente'
            })
            
        except Talle.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Talle no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def eliminar_color_rapido(request):
    """Eliminar color desde AJAX (solo si no está en uso)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        color_id = request.POST.get('id')
        
        try:
            color = Color.objects.get(id=color_id)
            color_nombre = color.nombre
            
            # Verificar si el color está siendo usado por algún producto
            if color.producto_set.exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'El color "{color_nombre}" está siendo usado por {color.producto_set.count()} productos. No se puede eliminar.'
                })
            
            # Eliminar el color
            color.delete()
            return JsonResponse({
                'success': True,
                'message': f'Color "{color_nombre}" eliminado correctamente'
            })
            
        except Color.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Color no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ==================== GESTIÓN DE ESTADO DE USUARIOS ====================

@login_required
@requiere_ver_usuarios
def cambiar_estado_usuario(request, id):
    """Cambiar el estado activo/inactivo de un usuario"""
    usuario = get_object_or_404(User, id=id)
    
    if usuario == request.user:
        messages.error(request, 'No puedes cambiar el estado de tu propia cuenta')
        return redirect('panel_admin:usuarios')
    
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para cambiar el estado de superusuarios')
        return redirect('panel_admin:usuarios')
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado') == 'activo'
        
        usuario.is_active = nuevo_estado
        usuario.save()
        
        estado_texto = 'activado' if nuevo_estado else 'desactivado'
        messages.success(request, f'Usuario "{usuario.username}" {estado_texto} correctamente')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'nuevo_estado': 'activo' if usuario.is_active else 'inactivo',
                'mensaje': f'Usuario {estado_texto} correctamente'
            })
        
        return redirect('panel_admin:usuarios')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=400)
    
    messages.error(request, 'Método no permitido')
    return redirect('panel_admin:usuarios')

def pedido_eliminar(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido.delete()
    messages.success(request, f"Pedido #{pedido_id} eliminado correctamente.")
    return redirect('panel_admin:pedidos')
