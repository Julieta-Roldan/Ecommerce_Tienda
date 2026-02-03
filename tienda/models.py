from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    # CAMPO NUEVO: imagen de fondo para la categoría
    imagen_fondo = models.ImageField(
        upload_to='categorias/',
        blank=True,
        null=True,
        help_text="Imagen de fondo para la categoría en la página principal (tamaño recomendado: 600x400px)"
    )
    creado = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Talle(models.Model):
    nombre = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Talle'
        verbose_name_plural = 'Talles'

    def __str__(self):
        return self.nombre

class Color(models.Model):
    nombre = models.CharField(max_length=30)
    codigo_hex = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        verbose_name = 'Color'
        verbose_name_plural = 'Colores'

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    talles = models.ManyToManyField(Talle, blank=True)
    colores = models.ManyToManyField(Color, blank=True)
    

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='productos/')
    orden = models.PositiveIntegerField(default=0)
    es_principal = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Imagen del producto'
        verbose_name_plural = 'Imágenes del producto'
        ordering = ['orden']
    
    def __str__(self):
        return f"Imagen de {self.producto.nombre}"

class Favorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'producto')

    def __str__(self):
        return f"{self.usuario.username} - {self.producto.nombre}"