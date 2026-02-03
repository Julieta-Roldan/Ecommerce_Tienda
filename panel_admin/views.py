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
from django.contrib.auth.models import User  # Importar aquí para usar en toda la vista
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib.auth.models import Group, Permission
from tienda.models import Talle, Color 


# ==================== DECORADORES PERSONALIZADOS ====================

def requiere_permiso(permiso_codename):
    """Decorador para verificar permisos específicos"""
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
    """Verifica si el usuario tiene acceso al panel admin"""
    # Superusuarios y staff siempre tienen acceso
    if user.is_superuser or user.is_staff:
        return True
    
    # Verificar si está en algún grupo con permisos
    grupos_con_acceso = ['Administradores', 'Empleados', 'Vendedores']
    return user.groups.filter(name__in=grupos_con_acceso).exists()

def admin_required(view_func):
    """Decorador para vistas solo de administradores"""
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
    """Verifica si el usuario puede ver el dashboard"""
    if user.is_superuser:
        return True
    # Empleados pueden ver dashboard si tienen permisos
    return user.groups.filter(name__in=['Administradores', 'Empleados']).exists()

def puede_gestionar_usuarios(user):
    """Verifica si el usuario puede gestionar usuarios"""
    return user.is_superuser or user.groups.filter(name='Administradores').exists()

# ==================== DECORADORES ESPECÍFICOS POR SECCIÓN ====================

def requiere_ver_productos(view_func):
    """Decorador para vistas de productos (solo Admin y Empleados)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_superuser or 
                request.user.groups.filter(name__in=['Administradores', 'Empleados']).exists()):
            messages.error(request, 'No tienes permisos para acceder a la sección de Productos')
            return redirect('panel_admin:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def requiere_ver_categorias(view_func):
    """Decorador para vistas de categorías (solo Admin y Empleados)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_superuser or 
                request.user.groups.filter(name__in=['Administradores', 'Empleados']).exists()):
            messages.error(request, 'No tienes permisos para acceder a la sección de Categorías')
            return redirect('panel_admin:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def requiere_ver_pedidos(view_func):
    """Decorador para vistas de pedidos (Admin, Empleados y Vendedores)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_superuser or 
                request.user.groups.filter(name__in=['Administradores', 'Empleados', 'Vendedores']).exists()):
            messages.error(request, 'No tienes permisos para acceder a la sección de Pedidos')
            return redirect('panel_admin:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def requiere_ver_estadisticas(view_func):
    """Decorador para vistas de estadísticas (solo Admin y Empleados)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_superuser or 
                request.user.groups.filter(name__in=['Administradores', 'Empleados']).exists()):
            messages.error(request, 'No tienes permisos para acceder a Estadísticas')
            return redirect('panel_admin:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ==================== AUTENTICACIÓN ====================
def login_panel(request):
    """Vista de login personalizada para el panel"""
    if request.user.is_authenticated and es_staff(request.user):
        return redirect('panel_admin:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and es_staff(user):
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username}!')
            return redirect('panel_admin:dashboard')
        else:
            messages.error(request, 'Credenciales inválidas o usuario no es staff')
    
    return render(request, 'panel_admin/login.html')

def logout_panel(request):
    """Logout personalizado"""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('panel_admin:login')

# ==================== DASHBOARD ====================
@login_required
@user_passes_test(puede_ver_dashboard)
def dashboard(request):
    """Dashboard principal del panel"""
    
    # Estadísticas generales
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_pagados = Pedido.objects.filter(estado='pagado').count()
   
    
    # Ventas del mes actual - USANDO F() expressions
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    ventas_mes = ItemPedido.objects.filter(
        pedido__estado__in=['pagado', 'enviado', 'entregado'],
        pedido__fecha_creacion__gte=inicio_mes
    ).aggregate(
        total=Sum(F('precio_unitario') * F('cantidad'), output_field=DecimalField(max_digits=12, decimal_places=2))
    )['total'] or 0
    
    # Pedidos recientes (últimos 5)
    pedidos_recientes = Pedido.objects.order_by('-fecha_creacion')[:5]
    
    # Productos con stock bajo (< 10 unidades)
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
    }
    
    return render(request, 'panel_admin/dashboard.html', context)

# ==================== PRODUCTOS ====================
@login_required
@user_passes_test(es_staff)
@requiere_ver_productos
def productos_lista(request):
    """Lista de productos con filtros y paginación"""
    productos = Producto.objects.all().order_by('-creado')
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    estado = request.GET.get('estado')
    if estado == 'activos':
        productos = productos.filter(activo=True)
    elif estado == 'inactivos':
        productos = productos.filter(activo=False)
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda)
        )
    
    # Paginación
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
    """Crear nuevo producto con talles y colores"""
    
    if request.method == 'POST':
        # Validar datos manualmente
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
                
                # MANEJAR TALLES (nuevo)
                talles_ids = request.POST.getlist('talles')
                if talles_ids:
                    talles = Talle.objects.filter(id__in=talles_ids)
                    producto.talles.set(talles)
                
                # MANEJAR COLORES (nuevo)
                colores_ids = request.POST.getlist('colores')
                if colores_ids:
                    colores = Color.objects.filter(id__in=colores_ids)
                    producto.colores.set(colores)
                
                # Manejo de imágenes
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
    
    # Si es GET o hay errores, mostrar formulario
    categorias = Categoria.objects.filter(activo=True)
    talles = Talle.objects.all()  # NUEVO
    colores = Color.objects.all()  # NUEVO
    
    return render(request, 'panel_admin/productos/form.html', {
        'categorias': categorias,
        'talles': talles,  # NUEVO
        'colores': colores,  # NUEVO
        'titulo': 'Nuevo Producto',
        'accion': 'Crear'
    })
@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def producto_editar(request, id):
    """Editar producto existente con talles y colores"""
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        # Validar datos manualmente
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
                
                # Actualizar producto
                producto.nombre = nombre
                producto.categoria = categoria
                producto.precio = precio
                producto.stock = stock
                producto.descripcion = descripcion
                producto.activo = activo
                producto.save()
                
                # MANEJAR TALLES (nuevo)
                talles_ids = request.POST.getlist('talles')
                if talles_ids:
                    talles = Talle.objects.filter(id__in=talles_ids)
                    producto.talles.set(talles)
                else:
                    producto.talles.clear()
                
                # MANEJAR COLORES (nuevo)
                colores_ids = request.POST.getlist('colores')
                if colores_ids:
                    colores = Color.objects.filter(id__in=colores_ids)
                    producto.colores.set(colores)
                else:
                    producto.colores.clear()
                
                # Manejo de imágenes
                if 'imagen_principal' in request.FILES:
                    # Eliminar imagen principal anterior si existe
                    producto.imagenes.filter(es_principal=True).delete()
                    # Crear nueva
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
    
    # Si es GET, mostrar formulario con datos actuales
    categorias = Categoria.objects.filter(activo=True)
    talles = Talle.objects.all()  # NUEVO
    colores = Color.objects.all()  # NUEVO
    
    return render(request, 'panel_admin/productos/form.html', {
        'producto': producto,
        'categorias': categorias,
        'talles': talles,  # NUEVO
        'colores': colores,  # NUEVO
        'titulo': f'Editar: {producto.nombre}',
        'accion': 'Actualizar'
    })
@login_required
@user_passes_test(es_staff)
@requiere_ver_productos  
def producto_eliminar(request, id):
    """Eliminar producto PERMANENTEMENTE"""
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        # GUARDAR DATOS PARA EL MENSAJE
        producto_nombre = producto.nombre
        categoria_nombre = producto.categoria.nombre
        
        # 1. ELIMINAR IMÁGENES del producto (IMPORTANTE: para liberar espacio en servidor)
        producto.imagenes.all().delete()
        
        # 2. ELIMINAR FAVORITOS asociados a este producto
        producto.favorito_set.all().delete()
        
        # 3. ELIMINAR RELACIONES ManyToMany (talles y colores)
        producto.talles.clear()
        producto.colores.clear()
        
        # 4. ELIMINAR EL PRODUCTO PERMANENTEMENTE
        producto.delete()
        
        messages.success(request, f'Producto "{producto_nombre}" ELIMINADO PERMANENTEMENTE de la categoría "{categoria_nombre}"')
        return redirect('panel_admin:productos')
    
    # Si es GET, mostrar formulario de confirmación
    return render(request, 'panel_admin/productos/confirmar_eliminar.html', {
        'producto': producto
    })
# ==================== PEDIDOS ====================
@login_required
@user_passes_test(es_staff)
@requiere_ver_pedidos 
def pedidos_lista(request):
    """Lista de pedidos con filtros"""
    pedidos = Pedido.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        pedidos = pedidos.filter(estado=estado)
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        pedidos = pedidos.filter(fecha_creacion__gte=fecha_desde)
    if fecha_hasta:
        pedidos = pedidos.filter(fecha_creacion__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(pedidos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Totales para estadísticas rápidas
    total_pendientes = Pedido.objects.filter(estado='pendiente').count()
    total_pagados = Pedido.objects.filter(estado='pagado').count()
    
    context = {
        'page_obj': page_obj,
        'total_pendientes': total_pendientes,
        'total_pagados': total_pagados,
        'filtro_estado': estado,
        'filtro_fecha_desde': fecha_desde,
        'filtro_fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'panel_admin/pedidos/lista.html', context)

@login_required
@user_passes_test(es_staff)
@requiere_ver_pedidos 
def pedido_detalle(request, id):
    """Detalle completo de un pedido"""
    pedido = get_object_or_404(Pedido, id=id)
    
    # Calcular total usando el método de base de datos
    total_pedido = pedido.get_total_db()
    
    # Si es POST, actualizar estado
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Pedido.ESTADOS).keys():
            estado_anterior = pedido.estado
            pedido.estado = nuevo_estado
            pedido.save()
            
            # Si cambia a "entregado", podemos liberar el carrito asociado
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
    """Cambiar estado de pedido (para AJAX o POST normal)"""
    pedido = get_object_or_404(Pedido, id=id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in dict(Pedido.ESTADOS).keys():
            estado_anterior = pedido.estado
            pedido.estado = nuevo_estado
            pedido.save()
            
            # Si cambia a "entregado" o "cancelado", podemos liberar el carrito asociado
            if nuevo_estado in ['entregado', 'cancelado'] and pedido.carrito:
                pedido.carrito.items.all().delete()
            
            # Si es AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'nuevo_estado': pedido.estado,
                    'estado_display': pedido.get_estado_display(),
                    'mensaje': f'Pedido #{pedido.id} cambiado a "{pedido.get_estado_display()}"'
                })
            else:
                # Si es POST normal, redirigir con mensaje
                messages.success(request, 
                    f'Pedido #{pedido.id} cambiado de "{estado_anterior}" a "{nuevo_estado}"'
                )
                return redirect('panel_admin:pedidos')
    
    # Si no es POST o hay error
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
@user_passes_test(es_staff)
@requiere_ver_estadisticas  # <-- CORREGIR: estaba @requiere_ver_pedidos
def estadisticas(request):
    """Página de estadísticas avanzadas"""
    hoy = timezone.now()
    
    # Ventas últimos 30 días usando ExpressionWrapper
    fecha_inicio = hoy - timedelta(days=30)
    
    # Calcular subtotal como expresión de base de datos
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
    
    # Productos más vendidos
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
    
    # Categorías más populares (simplificado)
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
    """Lista de categorías con estadísticas"""
    categorias = Categoria.objects.all().order_by('-creado', 'nombre')  # Ordenar por fecha de creación primero
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        categorias = categorias.filter(nombre__icontains=busqueda)
    
    # Filtros adicionales
    estado = request.GET.get('estado')
    if estado == 'activas':
        categorias = categorias.filter(activo=True)
    elif estado == 'inactivas':
        categorias = categorias.filter(activo=False)
    elif estado == 'con_productos':
        categorias = categorias.annotate(num_productos=Count('producto')).filter(num_productos__gt=0)
    elif estado == 'sin_productos':
        categorias = categorias.annotate(num_productos=Count('producto')).filter(num_productos=0)
    
    # Calcular estadísticas para las tarjetas
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
    """Crear nueva categoría"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        activo = request.POST.get('activo') == 'on'  # AGREGAR esta línea
        
        if nombre:
            # Crear la categoría sin imagen primero
            categoria = Categoria.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                activo=activo  # AGREGAR este campo
            )
            
            # Manejar la imagen de fondo si se subió
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
    """Editar categoría existente"""
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        activo = request.POST.get('activo') == 'on'
        
        if nombre:
            categoria.nombre = nombre
            categoria.descripcion = descripcion
            categoria.activo = activo
            
            # Manejar la imagen de fondo
            if 'imagen_fondo' in request.FILES:
                imagen = request.FILES['imagen_fondo']
                categoria.imagen_fondo = imagen
            
            # Manejar la eliminación de imagen si se solicitó
            if 'quitar_imagen' in request.POST and request.POST['quitar_imagen'] == 'true':
                categoria.imagen_fondo.delete(save=False)  # Eliminar el archivo
                categoria.imagen_fondo = None  # Limpiar el campo
            
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
    """Eliminar categoría (con opciones si tiene productos)"""
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        categoria_nombre = categoria.nombre
        accion = request.POST.get('accion')
        
        if accion == 'desactivar':
            # Solo desactivar la categoría
            categoria.activo = False
            categoria.save()
            messages.success(request, f'Categoría "{categoria_nombre}" desactivada correctamente')
            return redirect('panel_admin:categorias')
        
        elif accion == 'eliminar':
            # Eliminar permanentemente (solo si no tiene productos)
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
            # Mover productos a otra categoría y luego eliminar
            nueva_categoria_id = request.POST.get('nueva_categoria')
            if nueva_categoria_id:
                try:
                    nueva_categoria = Categoria.objects.get(id=nueva_categoria_id)
                    # Mover todos los productos
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
    
    # Si es GET, mostrar formulario de confirmación
    otras_categorias = Categoria.objects.exclude(id=id).filter(activo=True)
    
    return render(request, 'panel_admin/categorias/confirmar_eliminar.html', {
        'categoria': categoria,
        'otras_categorias': otras_categorias,
    })

# ==================== USUARIOS/EMPLEADOS ====================
@login_required
@user_passes_test(puede_gestionar_usuarios)
def usuarios_lista(request):
    """Lista de usuarios (empleados) con estadísticas"""
    usuarios = User.objects.all().order_by('-date_joined')
    
    # Filtros
    tipo = request.GET.get('tipo')
    if tipo == 'staff':
        usuarios = usuarios.filter(is_staff=True)
    elif tipo == 'superusers':
        usuarios = usuarios.filter(is_superuser=True)
    elif tipo == 'activos':
        usuarios = usuarios.filter(is_active=True)
    elif tipo == 'inactivos':
        usuarios = usuarios.filter(is_active=False)
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda) |
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(usuarios, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
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
@user_passes_test(puede_gestionar_usuarios)
def usuario_nuevo(request):
    """Crear nuevo usuario (empleado)"""
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        # Obtener grupos seleccionados
        grupos_ids = request.POST.getlist('groups')
        grupos = Group.objects.filter(id__in=grupos_ids)
        
        # Obtener permisos individuales (solo superuser)
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
                    
                    # Asignar grupos
                    user.groups.set(grupos)
                    
                    # Asignar permisos individuales (solo superuser)
                    if request.user.is_superuser:
                        user.user_permissions.set(permisos)
                    
                    messages.success(request, f'Usuario "{user.username}" creado correctamente')
                    return redirect('panel_admin:usuarios')
                    
                except Exception as e:
                    messages.error(request, f'Error al crear usuario: {str(e)}')
        else:
            messages.error(request, 'Nombre de usuario y contraseña son requeridos')
    
    # Obtener grupos y permisos para el formulario
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
@user_passes_test(puede_gestionar_usuarios)
def usuario_editar(request, id):
    """Editar usuario existente"""
    usuario = get_object_or_404(User, id=id)
    
    # No permitir editar superusuarios a menos que seas superuser
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para editar superusuarios')
        return redirect('panel_admin:usuarios')
    
    # No permitir que empleados editen administradores
    if not request.user.is_superuser and usuario.groups.filter(name='Administradores').exists():
        messages.error(request, 'No puedes editar a otros administradores')
        return redirect('panel_admin:usuarios')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        # Obtener grupos seleccionados
        grupos_ids = request.POST.getlist('groups')
        grupos = Group.objects.filter(id__in=grupos_ids)
        
        # Obtener permisos individuales (solo superuser)
        permisos_ids = []
        if request.user.is_superuser:
            permisos_ids = request.POST.getlist('user_permissions')
        permisos = Permission.objects.filter(id__in=permisos_ids)
        
        usuario.email = email
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.is_staff = is_staff
        usuario.is_active = is_active
        
        # Cambiar contraseña si se proporcionó
        nueva_password = request.POST.get('password')
        if nueva_password:
            usuario.set_password(nueva_password)
        
        usuario.save()
        
        # Actualizar grupos
        usuario.groups.set(grupos)
        
        # Actualizar permisos individuales (solo superuser)
        if request.user.is_superuser:
            usuario.user_permissions.set(permisos)
        
        messages.success(request, f'Usuario "{usuario.username}" actualizado correctamente')
        return redirect('panel_admin:usuarios')
    
    # Obtener grupos y permisos para el formulario
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
@user_passes_test(es_staff)
def usuario_eliminar(request, id):
    """Eliminar usuario permanentemente"""
    usuario = get_object_or_404(User, id=id)
    
    # Verificaciones de seguridad
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta')
        return redirect('panel_admin:usuarios')
    
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para eliminar superusuarios')
        return redirect('panel_admin:usuarios')
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado correctamente')
        return redirect('panel_admin:usuarios')
    
    return render(request, 'panel_admin/usuarios/confirmar_eliminar.html', {
        'usuario': usuario
    })

@login_required
@user_passes_test(es_staff)
def cambiar_estado_usuario(request, id):
    """Activar/desactivar usuario"""
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=id)
        
        # No permitir modificar superusuarios a menos que seas superuser
        if usuario.is_superuser and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
        
        # No permitir desactivarse a sí mismo
        if usuario == request.user:
            return JsonResponse({'success': False, 'error': 'No puedes desactivarte a ti mismo'}, status=400)
        
        nuevo_estado = request.POST.get('estado') == 'true'
        usuario.is_active = nuevo_estado
        usuario.save()
        
        return JsonResponse({
            'success': True, 
            'nuevo_estado': usuario.is_active,
            'mensaje': f'Usuario {"activado" if usuario.is_active else "desactivado"} correctamente'
        })
    
    return JsonResponse({'success': False}, status=400)

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