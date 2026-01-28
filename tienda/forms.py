# tienda/forms.py
from django import forms
from .models import Producto, Categoria

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['categoria', 'nombre', 'descripcion', 'precio', 'stock', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
        }