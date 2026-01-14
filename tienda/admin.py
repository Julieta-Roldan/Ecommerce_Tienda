from django.contrib import admin

# Register your models here.
from .models import Categoria, Producto, Color, Talle, ImagenProducto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    # list_filter = ('activo',)
    # search_fields = ('nombre',)


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