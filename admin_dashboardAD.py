from bd import consultar_todos, consultar_uno


def obtener_resumen_dashboard():
    inventario = consultar_uno(
        """
        SELECT COUNT(*) AS productos,
               COALESCE(SUM(
                   stock_minimo > 0
                   AND (stock_actual + (stock_cajas_cerradas * unidades_por_caja)) <= stock_minimo
               ), 0) AS alertas_stock
        FROM productos
        """
    )
    usuarios = consultar_uno(
        "SELECT COUNT(*) AS usuarios_activos FROM usuarios WHERE estado = 'activo'"
    )
    return {
        "productos": inventario["productos"],
        "entradas_mes": _entradas_mes(),
        "salidas_mes": _salidas_mes(),
        "alertas_stock": int(inventario["alertas_stock"]),
        "usuarios_activos": usuarios["usuarios_activos"],
    }


def _entradas_mes():
    fila = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM entradas_stock
        WHERE YEAR(creado_en) = YEAR(CURDATE())
          AND MONTH(creado_en) = MONTH(CURDATE())
        """
    )
    return fila["total"]


def _salidas_mes():
    fila = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM salidas_stock
        WHERE YEAR(creado_en) = YEAR(CURDATE())
          AND MONTH(creado_en) = MONTH(CURDATE())
          AND COALESCE(estado, 'activa') = 'activa'
        """
    )
    return fila["total"]


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
    filas = consultar_todos(
        """
        SELECT m.tipo, m.descripcion AS detalle, m.fecha,
               COALESCE(u.nombre, 'Usuario eliminado') AS usuario
        FROM movimientos m
        LEFT JOIN usuarios u ON u.id = m.usuario_id
        ORDER BY m.id DESC
        LIMIT 6
        """
    )
    if not filas:
        return [{"tipo": "Entrada", "detalle": "Sin movimientos registrados todavia", "fecha": "-"}]
    return [dict(fila) for fila in filas]


def obtener_serie_movimientos():
    entradas = consultar_todos(
        """
        SELECT DATE(creado_en) AS fecha, COUNT(*) AS entradas
        FROM entradas_stock
        WHERE creado_en >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)
        GROUP BY DATE(creado_en)
        """
    )
    salidas = consultar_todos(
        """
        SELECT DATE(creado_en) AS fecha, COUNT(*) AS salidas
        FROM salidas_stock
        WHERE creado_en >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)
          AND COALESCE(estado, 'activa') = 'activa'
        GROUP BY DATE(creado_en)
        """
    )
    entradas_por_fecha = {str(fila["fecha"]): fila["entradas"] for fila in entradas}
    salidas_por_fecha = {str(fila["fecha"]): fila["salidas"] for fila in salidas}
    dias = consultar_todos(
        """
        SELECT DATE_SUB(CURDATE(), INTERVAL n.n DAY) AS fecha,
               ELT(WEEKDAY(DATE_SUB(CURDATE(), INTERVAL n.n DAY)) + 1, 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom') AS dia
        FROM (
          SELECT 5 AS n UNION ALL SELECT 4 UNION ALL SELECT 3
          UNION ALL SELECT 2 UNION ALL SELECT 1 UNION ALL SELECT 0
        ) n
        ORDER BY fecha
        """
    )
    maximo = max(
        [int(valor) for valor in entradas_por_fecha.values()]
        + [int(valor) for valor in salidas_por_fecha.values()]
        + [1]
    )
    return [
        {
            "dia": fila["dia"],
            "entradas": round((int(entradas_por_fecha.get(str(fila["fecha"]), 0)) / maximo) * 100),
            "salidas": round((int(salidas_por_fecha.get(str(fila["fecha"]), 0)) / maximo) * 100),
        }
        for fila in dias
    ]
