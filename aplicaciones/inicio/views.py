from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def navegacion_principal():
    return [
        {'etiqueta': 'Panel', 'icono': 'dashboard', 'url': 'panel', 'activo': True},
        {'etiqueta': 'Productos', 'icono': 'inventory_2', 'url': '#', 'activo': False},
        {'etiqueta': 'Entradas', 'icono': 'move_to_inbox', 'url': '#', 'activo': False},
        {'etiqueta': 'Salidas', 'icono': 'outbox', 'url': '#', 'activo': False},
        {'etiqueta': 'Proveedores', 'icono': 'local_shipping', 'url': '#', 'activo': False},
        {'etiqueta': 'Reportes', 'icono': 'monitoring', 'url': '#', 'activo': False},
    ]


@login_required
def panel(request):
    rol = 'Administrador' if request.user.is_superuser else 'Responsable de almacen'
    contexto = {
        'pagina_titulo': 'Panel de almacen',
        'pagina_subtitulo': 'Vista operativa para controlar repuestos, movimientos y alertas del almacen automotriz.',
        'rol': rol,
        'elementos_navegacion': navegacion_principal(),
        'tarjetas_resumen': [
            {'titulo': 'Productos registrados', 'valor': '0', 'detalle': 'catalogo inicial', 'icono': 'inventory_2'},
            {'titulo': 'Entradas del mes', 'valor': '0', 'detalle': 'compras o reposiciones', 'icono': 'move_to_inbox'},
            {'titulo': 'Salidas del mes', 'valor': '0', 'detalle': 'ventas o entregas', 'icono': 'outbox'},
            {'titulo': 'Alertas de stock', 'valor': '0', 'detalle': 'productos por revisar', 'icono': 'warning'},
        ],
        'alertas': [
            {
                'titulo': 'Catalogo pendiente',
                'detalle': 'El siguiente modulo sera registrar productos, marcas y categorias.',
                'icono': 'playlist_add',
            },
            {
                'titulo': 'Stock minimo',
                'detalle': 'Se configuraran alertas cuando un repuesto llegue a su minimo.',
                'icono': 'notification_important',
            },
        ],
        'movimientos_recientes': [
            {'tipo': 'Entrada', 'detalle': 'Sin movimientos registrados todavia', 'fecha': '-'},
            {'tipo': 'Salida', 'detalle': 'Sin movimientos registrados todavia', 'fecha': '-'},
        ],
    }
    return render(request, 'admin/panel.html', contexto)
