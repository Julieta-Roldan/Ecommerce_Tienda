from django.contrib import admin

# Register your models here.
from .models import Categoria, Producto, Color, Talle, ImagenProducto
from django.utils.html import mark_safe

# tienda/admin.py 
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'creado', 'imagen_fondo_preview')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('creado', 'actualizado', 'imagen_fondo_preview')
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Imagen de fondo', {
            'fields': ('imagen_fondo', 'imagen_fondo_preview'),
            'description': 'Imagen que aparecerá como fondo en la página principal'
        }),
        ('Fechas', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )

    def imagen_fondo_preview(self, obj):
        if obj.imagen_fondo:
            return mark_safe(f'<img src="{obj.imagen_fondo.url}" style="max-height: 100px;" />')
        return "Sin imagen"
    imagen_fondo_preview.short_description = "Vista previa"

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'activo')
    # list_filter = ('categoria', 'activo')
    # search_fields = ('nombre',)
    
    #yo

# ... lo que ya escribió tu compañera queda igual ...

admin.site.register(Color)
admin.site.register(Talle)
admin.site.register(ImagenProducto)