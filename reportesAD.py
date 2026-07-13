from datetime import date, datetime, timedelta

from bd import consultar_todos, consultar_uno


def _fecha_valida(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalizar_filtros_reportes(filtros):
    hoy = date.today()
    inicio = _fecha_valida(filtros.get("fecha_inicio")) or hoy.replace(day=1)
    fin = _fecha_valida(filtros.get("fecha_fin")) or hoy
    if inicio > fin:
        inicio, fin = fin, inicio
    return {
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
    }


def _parametros_fecha(filtros):
    return (filtros["fecha_inicio"], filtros["fecha_fin"])


def obtener_reporte_general(filtros):
    filtros = normalizar_filtros_reportes(filtros)
    return {
        "filtros": filtros,
        "resumen": _resumen_reportes(filtros),
        "stock_critico": _stock_critico(),
        "movimientos_dia": _movimientos_por_dia(filtros),
        "top_salidas": _productos_mas_retirados(filtros),
        "salidas_vehiculos": _salidas_por_vehiculo(filtros),
        "entradas_proveedores": _entradas_por_proveedor(filtros),
        "stock_tipos": _stock_por_tipo(),
        "ajustes_recientes": _ajustes_recientes(filtros),
    }


def _resumen_reportes(filtros):
    inventario = consultar_uno(
        """
        SELECT COUNT(*) AS productos,
               COALESCE(SUM(stock_actual > 0 OR stock_baldes_cerrados > 0 OR baldes_abiertos > 0), 0) AS con_stock,
               COALESCE(SUM(stock_actual <= 0 AND stock_baldes_cerrados <= 0 AND baldes_abiertos <= 0), 0) AS sin_stock,
               COALESCE(SUM(stock_actual > 0 AND stock_minimo > 0 AND stock_actual <= stock_minimo), 0) AS bajo_stock,
               COALESCE(SUM(stock_baldes_cerrados), 0) AS baldes_cerrados,
               COALESCE(SUM(baldes_abiertos), 0) AS baldes_en_uso
        FROM productos
        """
    )
    entradas = consultar_uno(
        """
        SELECT COUNT(*) AS entradas,
               COUNT(DISTINCT producto_id) AS productos_entrada
        FROM entradas_stock
        WHERE DATE(creado_en) BETWEEN %s AND %s
        """,
        _parametros_fecha(filtros),
    )
    salidas = consultar_uno(
        """
        SELECT COUNT(DISTINCT s.id) AS salidas,
               COUNT(d.id) AS lineas_salida,
               COUNT(DISTINCT d.producto_id) AS productos_salida
        FROM salidas_stock s
        LEFT JOIN salidas_stock_detalle d ON d.salida_id = s.id
        WHERE DATE(s.creado_en) BETWEEN %s AND %s
        """,
        _parametros_fecha(filtros),
    )
    return {
        "productos": inventario["productos"],
        "con_stock": int(inventario["con_stock"]),
        "sin_stock": int(inventario["sin_stock"]),
        "bajo_stock": int(inventario["bajo_stock"]),
        "baldes_cerrados": inventario["baldes_cerrados"],
        "baldes_en_uso": inventario["baldes_en_uso"],
        "entradas": entradas["entradas"],
        "productos_entrada": entradas["productos_entrada"],
        "salidas": salidas["salidas"],
        "lineas_salida": salidas["lineas_salida"],
        "productos_salida": salidas["productos_salida"],
    }


def _stock_critico():
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT p.nombre, p.marca, p.stock_actual, p.stock_minimo,
                   p.stock_suelto, p.baldes_abiertos, p.stock_baldes_cerrados,
                   t.nombre AS tipo, c.nombre AS categoria, u.abreviatura
            FROM productos p
            INNER JOIN tipos_producto t ON t.id = p.tipo_id
            INNER JOIN categorias c ON c.id = p.categoria_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            WHERE (p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo)
               OR (p.stock_actual <= 0 AND p.baldes_abiertos <= 0 AND p.stock_baldes_cerrados <= 0)
            ORDER BY
              (p.stock_actual <= 0 AND p.baldes_abiertos <= 0 AND p.stock_baldes_cerrados <= 0) DESC,
              p.stock_actual ASC,
              p.nombre
            LIMIT 12
            """
        )
    ]


def _productos_mas_retirados(filtros):
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT p.nombre, p.marca, t.nombre AS tipo, c.nombre AS categoria,
                   u.abreviatura, COUNT(d.id) AS movimientos,
                   COALESCE(SUM(d.cantidad_base), 0) AS cantidad
            FROM salidas_stock_detalle d
            INNER JOIN salidas_stock s ON s.id = d.salida_id
            INNER JOIN productos p ON p.id = d.producto_id
            INNER JOIN tipos_producto t ON t.id = p.tipo_id
            INNER JOIN categorias c ON c.id = p.categoria_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            WHERE DATE(s.creado_en) BETWEEN %s AND %s
            GROUP BY p.id, p.nombre, p.marca, t.nombre, c.nombre, u.abreviatura
            ORDER BY cantidad DESC, movimientos DESC, p.nombre
            LIMIT 8
            """,
            _parametros_fecha(filtros),
        )
    ]


def _salidas_por_vehiculo(filtros):
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT s.placa, COALESCE(s.modelo, 'Sin modelo') AS modelo,
                   s.trabajador, COUNT(DISTINCT s.id) AS salidas,
                   COUNT(d.id) AS productos, MAX(s.creado_en) AS ultimo_movimiento
            FROM salidas_stock s
            LEFT JOIN salidas_stock_detalle d ON d.salida_id = s.id
            WHERE DATE(s.creado_en) BETWEEN %s AND %s
            GROUP BY s.placa, s.modelo, s.trabajador
            ORDER BY salidas DESC, productos DESC, ultimo_movimiento DESC
            LIMIT 8
            """,
            _parametros_fecha(filtros),
        )
    ]


def _entradas_por_proveedor(filtros):
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT COALESCE(NULLIF(proveedor, ''), 'Sin proveedor') AS proveedor,
                   COUNT(*) AS entradas,
                   COUNT(DISTINCT producto_id) AS productos,
                   MAX(creado_en) AS ultima_entrada
            FROM entradas_stock
            WHERE DATE(creado_en) BETWEEN %s AND %s
            GROUP BY COALESCE(NULLIF(proveedor, ''), 'Sin proveedor')
            ORDER BY entradas DESC, productos DESC, ultima_entrada DESC
            LIMIT 8
            """,
            _parametros_fecha(filtros),
        )
    ]


def _stock_por_tipo():
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT t.nombre AS tipo, COUNT(p.id) AS productos,
                   COALESCE(SUM(p.stock_actual > 0 OR p.stock_baldes_cerrados > 0 OR p.baldes_abiertos > 0), 0) AS con_stock,
                   COALESCE(SUM(p.stock_actual > 0 AND p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo), 0) AS bajo_stock,
                   COALESCE(SUM(p.stock_actual <= 0 AND p.stock_baldes_cerrados <= 0 AND p.baldes_abiertos <= 0), 0) AS sin_stock
            FROM tipos_producto t
            LEFT JOIN productos p ON p.tipo_id = t.id
            GROUP BY t.id, t.nombre
            ORDER BY t.id
            """
        )
    ]


def _movimientos_por_dia(filtros):
    entradas = consultar_todos(
        """
        SELECT DATE(creado_en) AS fecha, COUNT(*) AS entradas
        FROM entradas_stock
        WHERE DATE(creado_en) BETWEEN %s AND %s
        GROUP BY DATE(creado_en)
        """,
        _parametros_fecha(filtros),
    )
    salidas = consultar_todos(
        """
        SELECT DATE(creado_en) AS fecha, COUNT(*) AS salidas
        FROM salidas_stock
        WHERE DATE(creado_en) BETWEEN %s AND %s
        GROUP BY DATE(creado_en)
        """,
        _parametros_fecha(filtros),
    )
    entradas_por_fecha = {fila["fecha"].isoformat(): int(fila["entradas"]) for fila in entradas}
    salidas_por_fecha = {fila["fecha"].isoformat(): int(fila["salidas"]) for fila in salidas}
    fechas_con_datos = sorted(set(entradas_por_fecha) | set(salidas_por_fecha))

    inicio = _fecha_valida(filtros["fecha_inicio"])
    fin = _fecha_valida(filtros["fecha_fin"])
    rango_dias = (fin - inicio).days if inicio and fin else 0
    if rango_dias <= 31:
        fechas = [(inicio + timedelta(days=dia)).isoformat() for dia in range(rango_dias + 1)]
    else:
        fechas = fechas_con_datos

    maximo = max(
        [entradas_por_fecha.get(fecha, 0) for fecha in fechas]
        + [salidas_por_fecha.get(fecha, 0) for fecha in fechas]
        + [1]
    )
    return [
        {
            "fecha": fecha,
            "entradas": entradas_por_fecha.get(fecha, 0),
            "salidas": salidas_por_fecha.get(fecha, 0),
            "entradas_pct": round((entradas_por_fecha.get(fecha, 0) / maximo) * 100),
            "salidas_pct": round((salidas_por_fecha.get(fecha, 0) / maximo) * 100),
        }
        for fecha in fechas
    ]


def _ajustes_recientes(filtros):
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT a.creado_en, a.diferencia, a.motivo,
                   p.nombre AS producto, p.marca, u.abreviatura,
                   COALESCE(us.nombre, 'Usuario eliminado') AS usuario
            FROM ajustes_stock a
            INNER JOIN productos p ON p.id = a.producto_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            LEFT JOIN usuarios us ON us.id = a.usuario_id
            WHERE DATE(a.creado_en) BETWEEN %s AND %s
            ORDER BY a.id DESC
            LIMIT 8
            """,
            _parametros_fecha(filtros),
        )
    ]
