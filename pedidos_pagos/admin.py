from django.contrib import admin
from .models import Pedido, ItemPedido, Pago

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    can_delete = False

    readonly_fields = (
        'producto',
        'mostrar_precio',
        'cantidad',
        'mostrar_subtotal',
    )

    fields = (
        'producto',
        'mostrar_precio',
        'cantidad',
        'mostrar_subtotal',
    )

    def mostrar_precio(self, obj):
        return obj.precio_unitario
    mostrar_precio.short_description = "Precio unitario"

    def mostrar_subtotal(self, obj):
        return obj.subtotal
    mostrar_subtotal.short_description = "Subtotal"

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'estado',
        'email',
        'telefono',
        'total',
        'fecha_creacion',
    )

    list_filter = (
        'estado',
        'fecha_creacion',
    )

    search_fields = (
        'email',
        'telefono',
    )

    readonly_fields = (
        'email',
        'telefono',
        'estado',
        'fecha_creacion',
        'total',
    )

    inlines = [ItemPedidoInline]




@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'pedido',
        'metodo',
        'monto',
        'estado',
        'fecha_creacion',
    )

    list_filter = (
        'estado',
        'metodo',
    )

    search_fields = (
        'pedido__id',
        'referencia_externa',
    )

    readonly_fields = (
        'pedido',
        'metodo',
        'monto',
        'referencia_externa',
        'fecha_creacion',
    )
