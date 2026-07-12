from bd import consultar_uno


def obtener_resumen_dashboard():
    inventario = consultar_uno(
        """
        SELECT COUNT(*) AS productos,
               COALESCE(SUM(stock_minimo > 0 AND stock_actual <= stock_minimo), 0) AS alertas_stock
        FROM productos
        """
    )
    usuarios = consultar_uno(
        "SELECT COUNT(*) AS usuarios_activos FROM usuarios WHERE estado = 'activo'"
    )
    return {
        "productos": inventario["productos"],
        "entradas_mes": 0,
        "salidas_mes": 0,
        "alertas_stock": int(inventario["alertas_stock"]),
        "usuarios_activos": usuarios["usuarios_activos"],
    }


def obtener_alertas_dashboard():
    return [
        {
            "titulo": "Catalogo en progreso",
            "detalle": "Registra los productos encontrados durante el conteo del almacen.",
            "icono": "inventory_2",
            "tipo": "info",
        },
        {
            "titulo": "Stock minimo",
            "detalle": "Las alertas apareceran cuando un producto alcance su cantidad minima.",
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
        {"dia": "Lun", "entradas": 0, "salidas": 0},
        {"dia": "Mar", "entradas": 0, "salidas": 0},
        {"dia": "Mie", "entradas": 0, "salidas": 0},
        {"dia": "Jue", "entradas": 0, "salidas": 0},
        {"dia": "Vie", "entradas": 0, "salidas": 0},
        {"dia": "Sab", "entradas": 0, "salidas": 0},
    ]
