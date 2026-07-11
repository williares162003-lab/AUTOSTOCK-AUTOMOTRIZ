def obtener_resumen_dashboard():
    return {
        "productos": 0,
        "entradas_mes": 0,
        "salidas_mes": 0,
        "alertas_stock": 0,
        "usuarios_activos": 2,
    }


def obtener_alertas_dashboard():
    return [
        {
            "titulo": "Catalogo pendiente",
            "detalle": "Registrar productos, marcas, categorias y ubicaciones.",
            "icono": "inventory_2",
            "tipo": "info",
        },
        {
            "titulo": "Stock minimo",
            "detalle": "Configurar alertas para repuestos con bajo inventario.",
            "icono": "notification_important",
            "tipo": "warning",
        },
    ]


def obtener_movimientos_recientes():
    return [
        {"tipo": "Entrada", "detalle": "Sin movimientos registrados todavia", "fecha": "-"},
        {"tipo": "Salida", "detalle": "Sin movimientos registrados todavia", "fecha": "-"},
    ]


def obtener_serie_movimientos():
    return [
        {"dia": "Lun", "entradas": 18, "salidas": 8},
        {"dia": "Mar", "entradas": 12, "salidas": 10},
        {"dia": "Mie", "entradas": 20, "salidas": 14},
        {"dia": "Jue", "entradas": 10, "salidas": 15},
        {"dia": "Vie", "entradas": 16, "salidas": 11},
        {"dia": "Sab", "entradas": 8, "salidas": 6},
    ]
