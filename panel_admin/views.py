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

# Verificador de staff
def es_staff(user):
    return user.is_staff or user.is_superuser

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
@user_passes_test(es_staff)
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
    
    context = {
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_pagados': pedidos_pagados,
        'ventas_mes': ventas_mes,
        'pedidos_recientes': pedidos_recientes,
        'productos_stock_bajo': productos_stock_bajo,
        'productos_sin_stock': productos_sin_stock,
    }
    
    return render(request, 'panel_admin/dashboard.html', context)

# ==================== PRODUCTOS ====================
@login_required
@user_passes_test(es_staff)
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
def producto_nuevo(request):
    """Crear nuevo producto (versión simplificada sin forms.py)"""
    
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
    return render(request, 'panel_admin/productos/form.html', {
        'categorias': categorias,
        'titulo': 'Nuevo Producto',
        'accion': 'Crear'
    })

@login_required
@user_passes_test(es_staff)
def producto_editar(request, id):
    """Editar producto existente (versión simplificada)"""
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
    return render(request, 'panel_admin/productos/form.html', {
        'producto': producto,
        'categorias': categorias,
        'titulo': f'Editar: {producto.nombre}',
        'accion': 'Actualizar'
    })

@login_required
@user_passes_test(es_staff)
def producto_eliminar(request, id):
    """Eliminar producto (soft delete)"""
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        producto_nombre = producto.nombre
        producto.activo = False
        producto.save()
        messages.success(request, f'Producto "{producto_nombre}" desactivado correctamente')
        return redirect('panel_admin:productos')
    
    return render(request, 'panel_admin/productos/confirmar_eliminar.html', {
        'producto': producto
    })

# ==================== PEDIDOS ====================
@login_required
@user_passes_test(es_staff)
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
def cambiar_estado_pedido(request, id):
    """Cambiar estado de pedido (para AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pedido = get_object_or_404(Pedido, id=id)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in dict(Pedido.ESTADOS).keys():
            pedido.estado = nuevo_estado
            pedido.save()
            return JsonResponse({'success': True, 'nuevo_estado': pedido.estado})
    
    return JsonResponse({'success': False}, status=400)

# ==================== ESTADÍSTICAS ====================
@login_required
@user_passes_test(es_staff)
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
def categorias_lista(request):
    """Lista de categorías"""
    categorias = Categoria.objects.all().order_by('nombre')
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        categorias = categorias.filter(nombre__icontains=busqueda)
    
    context = {
        'categorias': categorias,
        'busqueda': busqueda,
    }
    
    return render(request, 'panel_admin/categorias/lista.html', context)

@login_required
@user_passes_test(es_staff)
def categoria_nueva(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        
        if nombre:
            categoria = Categoria.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                activo=True
            )
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
def categoria_eliminar(request, id):
    """Eliminar categoría (soft delete)"""
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        categoria_nombre = categoria.nombre
        
        # Verificar si hay productos en esta categoría
        if categoria.producto_set.exists():
            messages.error(request, 
                f'No se puede eliminar la categoría "{categoria_nombre}" porque tiene productos asociados. '
                'Primero mueve o elimina los productos.'
            )
            return redirect('panel_admin:categorias')
        
        categoria.delete()
        messages.success(request, f'Categoría "{categoria_nombre}" eliminada correctamente')
        return redirect('panel_admin:categorias')
    
    return render(request, 'panel_admin/categorias/confirmar_eliminar.html', {
        'categoria': categoria
    })
    
    # ==================== USUARIOS/EMPLEADOS ====================
@login_required
@user_passes_test(es_staff)
def usuarios_lista(request):
    """Lista de usuarios (empleados)"""
    from django.contrib.auth.models import User
    
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
    
    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'filtro_tipo': tipo,
    }
    
    return render(request, 'panel_admin/usuarios/lista.html', context)

@login_required
@user_passes_test(es_staff)
def usuario_nuevo(request):
    """Crear nuevo usuario (empleado)"""
    from django.contrib.auth.models import User
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        if username and password:
            # Verificar si el usuario ya existe
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe')
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_active=is_active
                )
                messages.success(request, f'Usuario "{user.username}" creado correctamente')
                return redirect('panel_admin:usuarios')
        else:
            messages.error(request, 'Nombre de usuario y contraseña son requeridos')
    
    return render(request, 'panel_admin/usuarios/form.html', {
        'titulo': 'Nuevo Usuario/Empleado',
        'accion': 'Crear'
    })

@login_required
@user_passes_test(es_staff)
def usuario_editar(request, id):
    """Editar usuario existente"""
    from django.contrib.auth.models import User
    usuario = get_object_or_404(User, id=id)
    
    # No permitir editar superusuarios a menos que seas superuser
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para editar superusuarios')
        return redirect('panel_admin:usuarios')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
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
        
        messages.success(request, f'Usuario "{usuario.username}" actualizado correctamente')
        return redirect('panel_admin:usuarios')
    
    return render(request, 'panel_admin/usuarios/form.html', {
        'titulo': f'Editar: {usuario.username}',
        'accion': 'Actualizar',
        'usuario': usuario
    })

@login_required
@user_passes_test(es_staff)
def cambiar_estado_usuario(request, id):
    """Activar/desactivar usuario"""
    from django.contrib.auth.models import User
    
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