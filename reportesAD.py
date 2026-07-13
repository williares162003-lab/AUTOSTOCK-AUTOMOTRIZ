import csv
from io import StringIO
from datetime import date, datetime, timedelta

from bd import consultar_todos, consultar_uno
from movimientos_kardexAD import listar_movimientos_kardex_con_errores


def _fecha_valida(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


def _placa_valida(valor):
    return (valor or "").strip().upper()[:20]


def normalizar_filtros_reportes(filtros):
    hoy = date.today()
    inicio = _fecha_valida(filtros.get("fecha_inicio")) or hoy
    fin = _fecha_valida(filtros.get("fecha_fin")) or hoy
    if inicio > fin:
        inicio, fin = fin, inicio
    return {
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
        "placa": _placa_valida(filtros.get("placa", "")),
    }


def _parametros_fecha(filtros):
    return (filtros["fecha_inicio"], filtros["fecha_fin"])


def _filtro_placa(filtros, alias="s"):
    placa = filtros.get("placa", "")
    if not placa:
        return "", ()
    return f" AND UPPER({alias}.placa) LIKE %s", (f"%{placa}%",)


def obtener_reporte_general(filtros):
    filtros = normalizar_filtros_reportes(filtros)
    actividad, errores_actividad = _actividad_periodo(filtros)
    return {
        "filtros": filtros,
        "atajos": _atajos_fecha(),
        "periodo_es_dia": filtros["fecha_inicio"] == filtros["fecha_fin"],
        "resumen": _resumen_reportes(filtros),
        "actividad": actividad,
        "errores_actividad": errores_actividad,
        "stock_critico": _stock_critico(),
        "movimientos_dia": _movimientos_por_dia(filtros),
        "top_salidas": _productos_mas_retirados(filtros),
        "salidas_vehiculos": _salidas_por_vehiculo(filtros),
        "detalle_placa": _detalle_por_placa(filtros),
        "entradas_recientes": _entradas_recientes(filtros),
        "stock_tipos": _stock_por_tipo(),
        "ajustes_recientes": _ajustes_recientes(filtros),
    }


def _atajos_fecha():
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    return {
        "hoy": {"inicio": hoy.isoformat(), "fin": hoy.isoformat()},
        "ayer": {"inicio": ayer.isoformat(), "fin": ayer.isoformat()},
        "semana": {"inicio": inicio_semana.isoformat(), "fin": hoy.isoformat()},
        "mes": {"inicio": hoy.replace(day=1).isoformat(), "fin": hoy.isoformat()},
    }


def generar_reporte_csv(filtros):
    reporte = obtener_reporte_general(filtros)
    contenido = StringIO()
    escritor = csv.writer(contenido)
    filtros = reporte["filtros"]

    escritor.writerow(["AUTOMAN Chiclayo E.I.R.L."])
    escritor.writerow(["Reporte de almacen"])
    escritor.writerow(["Desde", filtros["fecha_inicio"], "Hasta", filtros["fecha_fin"]])
    if filtros["placa"]:
        escritor.writerow(["Placa", filtros["placa"]])
    escritor.writerow([])

    escritor.writerow(["Resumen"])
    resumen = reporte["resumen"]
    escritor.writerow(["Productos", resumen["productos"]])
    escritor.writerow(["Con stock", resumen["con_stock"]])
    escritor.writerow(["Sin stock", resumen["sin_stock"]])
    escritor.writerow(["Bajo minimo", resumen["bajo_stock"]])
    escritor.writerow(["Entradas", resumen["entradas"]])
    escritor.writerow(["Salidas", resumen["salidas"]])
    escritor.writerow(["Lineas de salida", resumen["lineas_salida"]])
    escritor.writerow(["Baldes cerrados", resumen["baldes_cerrados"]])
    escritor.writerow(["Baldes en uso", resumen["baldes_en_uso"]])
    escritor.writerow(["Cilindros cerrados", resumen["cilindros_cerrados"]])
    escritor.writerow(["Cilindros en uso", resumen["cilindros_en_uso"]])
    escritor.writerow([])

    escritor.writerow(["Actividad"])
    escritor.writerow(["Fecha", "Movimiento", "Producto", "Marca", "Origen", "Detalle", "Entrada", "Salida", "Unidad", "Usuario"])
    for movimiento in reporte["actividad"]:
        escritor.writerow(
            [
                movimiento["fecha"],
                movimiento["tipo"],
                movimiento["producto"],
                movimiento["marca"] or "Sin marca",
                movimiento["origen"],
                movimiento["detalle"],
                movimiento["entrada"] or "",
                movimiento["salida"] or "",
                movimiento["unidad"],
                movimiento["usuario"],
            ]
        )
    escritor.writerow([])

    escritor.writerow(["Productos mas retirados"])
    escritor.writerow(["Producto", "Marca", "Categoria", "Cantidad", "Unidad", "Movimientos"])
    for producto in reporte["top_salidas"]:
        escritor.writerow(
            [
                producto["nombre"],
                producto["marca"] or "Sin marca",
                producto["categoria"],
                producto["cantidad"],
                producto["abreviatura"],
                producto["movimientos"],
            ]
        )
    escritor.writerow([])

    escritor.writerow(["Salidas por vehiculo"])
    escritor.writerow(["Placa", "Modelo", "Trabajador", "Salidas", "Items", "Ultimo movimiento"])
    for salida in reporte["salidas_vehiculos"]:
        escritor.writerow(
            [
                salida["placa"],
                salida["modelo"],
                salida["trabajador"],
                salida["salidas"],
                salida["productos"],
                salida["ultimo_movimiento"],
            ]
        )
    escritor.writerow([])

    if filtros["placa"]:
        escritor.writerow([f"Detalle de placa {filtros['placa']}"])
        escritor.writerow(["Fecha", "Placa", "Modelo", "Trabajador", "Producto", "Marca", "Cantidad", "Unidad", "Origen", "Usuario"])
        for detalle in reporte["detalle_placa"]:
            escritor.writerow(
                [
                    detalle["creado_en"],
                    detalle["placa"],
                    detalle["modelo"] or "",
                    detalle["trabajador"],
                    detalle["producto"],
                    detalle["marca"] or "Sin marca",
                    detalle["cantidad"],
                    detalle["abreviatura"],
                    detalle["origen_texto"],
                    detalle["usuario"],
                ]
            )
        escritor.writerow([])

    escritor.writerow(["Entradas recientes"])
    escritor.writerow(["Fecha", "Producto", "Marca", "Entrada", "Unidad", "Documento", "Motivo", "Usuario"])
    for entrada in reporte["entradas_recientes"]:
        es_balde = entrada["origen_stock"] == "balde_cerrado"
        es_cilindro = entrada["origen_stock"] == "cilindro_cerrado"
        escritor.writerow(
            [
                entrada["creado_en"],
                entrada["producto"],
                entrada["marca"] or "Sin marca",
                entrada["cantidad"] if es_balde or es_cilindro else entrada["cantidad_base"],
                "balde(s)" if es_balde else ("cilindro(s)" if es_cilindro else entrada["abreviatura"]),
                entrada["documento"] or "",
                entrada["motivo"],
                entrada["usuario"],
            ]
        )
    escritor.writerow([])

    escritor.writerow(["Productos que requieren atencion"])
    escritor.writerow(["Producto", "Marca", "Tipo", "Categoria", "Disponible", "Minimo", "Unidad", "Baldes cerrados", "Baldes en uso", "Cilindros cerrados", "Cilindros en uso"])
    for producto in reporte["stock_critico"]:
        escritor.writerow(
            [
                producto["nombre"],
                producto["marca"] or "Sin marca",
                producto["tipo"],
                producto["categoria"],
                producto["stock_actual"],
                producto["stock_minimo"],
                producto["abreviatura"],
                producto["stock_baldes_cerrados"],
                producto["baldes_abiertos"],
                producto["stock_cilindros_cerrados"],
                producto["cilindros_abiertos"],
            ]
        )

    placa = f"-{filtros['placa']}" if filtros["placa"] else ""
    nombre = f"reporte-automan{placa}-{filtros['fecha_inicio']}-a-{filtros['fecha_fin']}.csv"
    return nombre, contenido.getvalue()


def _actividad_periodo(filtros):
    movimientos, errores = listar_movimientos_kardex_con_errores(
        {
            "fecha_inicio": filtros["fecha_inicio"],
            "fecha_fin": filtros["fecha_fin"],
            "tipo": "",
            "producto_id": "",
            "placa": filtros["placa"],
        }
    )
    return movimientos[:120], errores


def _resumen_reportes(filtros):
    inventario = consultar_uno(
        """
        SELECT COUNT(*) AS productos,
               COALESCE(SUM(stock_actual > 0 OR stock_baldes_cerrados > 0 OR baldes_abiertos > 0 OR stock_cilindros_cerrados > 0 OR cilindros_abiertos > 0), 0) AS con_stock,
               COALESCE(SUM(stock_actual <= 0 AND stock_baldes_cerrados <= 0 AND baldes_abiertos <= 0 AND stock_cilindros_cerrados <= 0 AND cilindros_abiertos <= 0), 0) AS sin_stock,
               COALESCE(SUM(stock_actual > 0 AND stock_minimo > 0 AND stock_actual <= stock_minimo), 0) AS bajo_stock,
               COALESCE(SUM(stock_baldes_cerrados), 0) AS baldes_cerrados,
               COALESCE(SUM(baldes_abiertos), 0) AS baldes_en_uso,
               COALESCE(SUM(stock_cilindros_cerrados), 0) AS cilindros_cerrados,
               COALESCE(SUM(cilindros_abiertos), 0) AS cilindros_en_uso
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
    placa_sql, placa_params = _filtro_placa(filtros)
    salidas = consultar_uno(
        f"""
        SELECT COUNT(DISTINCT s.id) AS salidas,
               COUNT(d.id) AS lineas_salida,
               COUNT(DISTINCT d.producto_id) AS productos_salida
        FROM salidas_stock s
        LEFT JOIN salidas_stock_detalle d ON d.salida_id = s.id
        WHERE DATE(s.creado_en) BETWEEN %s AND %s
        {placa_sql}
        """,
        _parametros_fecha(filtros) + placa_params,
    )
    return {
        "productos": inventario["productos"],
        "con_stock": int(inventario["con_stock"]),
        "sin_stock": int(inventario["sin_stock"]),
        "bajo_stock": int(inventario["bajo_stock"]),
        "baldes_cerrados": inventario["baldes_cerrados"],
        "baldes_en_uso": inventario["baldes_en_uso"],
        "cilindros_cerrados": inventario["cilindros_cerrados"],
        "cilindros_en_uso": inventario["cilindros_en_uso"],
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
                   p.cilindros_abiertos, p.stock_cilindros_cerrados,
                   t.nombre AS tipo, c.nombre AS categoria, u.abreviatura
            FROM productos p
            INNER JOIN tipos_producto t ON t.id = p.tipo_id
            INNER JOIN categorias c ON c.id = p.categoria_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            WHERE (p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo)
               OR (p.stock_actual <= 0 AND p.baldes_abiertos <= 0 AND p.stock_baldes_cerrados <= 0 AND p.cilindros_abiertos <= 0 AND p.stock_cilindros_cerrados <= 0)
            ORDER BY
              (p.stock_actual <= 0 AND p.baldes_abiertos <= 0 AND p.stock_baldes_cerrados <= 0 AND p.cilindros_abiertos <= 0 AND p.stock_cilindros_cerrados <= 0) DESC,
              p.stock_actual ASC,
              p.nombre
            LIMIT 12
            """
        )
    ]


def _productos_mas_retirados(filtros):
    placa_sql, placa_params = _filtro_placa(filtros)
    return [
        dict(fila)
        for fila in consultar_todos(
            f"""
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
            {placa_sql}
            GROUP BY p.id, p.nombre, p.marca, t.nombre, c.nombre, u.abreviatura
            ORDER BY cantidad DESC, movimientos DESC, p.nombre
            LIMIT 8
            """,
            _parametros_fecha(filtros) + placa_params,
        )
    ]


def _salidas_por_vehiculo(filtros):
    placa_sql, placa_params = _filtro_placa(filtros)
    return [
        dict(fila)
        for fila in consultar_todos(
            f"""
            SELECT s.placa, COALESCE(s.modelo, 'Sin modelo') AS modelo,
                   s.trabajador, COUNT(DISTINCT s.id) AS salidas,
                   COUNT(d.id) AS productos, MAX(s.creado_en) AS ultimo_movimiento
            FROM salidas_stock s
            LEFT JOIN salidas_stock_detalle d ON d.salida_id = s.id
            WHERE DATE(s.creado_en) BETWEEN %s AND %s
            {placa_sql}
            GROUP BY s.placa, s.modelo, s.trabajador
            ORDER BY salidas DESC, productos DESC, ultimo_movimiento DESC
            LIMIT 8
            """,
            _parametros_fecha(filtros) + placa_params,
        )
    ]


def _detalle_por_placa(filtros):
    if not filtros.get("placa"):
        return []
    placa_sql, placa_params = _filtro_placa(filtros)
    filas = consultar_todos(
        f"""
        SELECT s.creado_en, s.placa, s.modelo, s.trabajador,
               p.nombre AS producto, p.marca, d.cantidad_base AS cantidad,
               d.origen_stock, u.abreviatura,
               COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM salidas_stock s
        INNER JOIN salidas_stock_detalle d ON d.salida_id = s.id
        INNER JOIN productos p ON p.id = d.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = s.usuario_id
        WHERE DATE(s.creado_en) BETWEEN %s AND %s
        {placa_sql}
        ORDER BY s.creado_en DESC, d.id DESC
        LIMIT 120
        """,
        _parametros_fecha(filtros) + placa_params,
    )
    origenes = {
        "suelto": "Stock suelto",
        "balde_abierto": "Balde abierto",
        "cilindro_abierto": "Cilindro abierto",
    }
    detalles = []
    for fila in filas:
        detalle = dict(fila)
        detalle["origen_texto"] = origenes.get(detalle["origen_stock"], "Stock suelto")
        detalles.append(detalle)
    return detalles


def _entradas_recientes(filtros):
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT e.creado_en, e.cantidad, e.cantidad_base, e.origen_stock,
                   e.presentacion_nombre, e.factor, e.documento, e.motivo,
                   p.nombre AS producto, p.marca, u.abreviatura,
                   COALESCE(us.nombre, 'Usuario eliminado') AS usuario
            FROM entradas_stock e
            INNER JOIN productos p ON p.id = e.producto_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            LEFT JOIN usuarios us ON us.id = e.usuario_id
            WHERE DATE(e.creado_en) BETWEEN %s AND %s
            ORDER BY e.id DESC
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
                   COALESCE(SUM(p.stock_actual > 0 OR p.stock_baldes_cerrados > 0 OR p.baldes_abiertos > 0 OR p.stock_cilindros_cerrados > 0 OR p.cilindros_abiertos > 0), 0) AS con_stock,
                   COALESCE(SUM(p.stock_actual > 0 AND p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo), 0) AS bajo_stock,
                   COALESCE(SUM(p.stock_actual <= 0 AND p.stock_baldes_cerrados <= 0 AND p.baldes_abiertos <= 0 AND p.stock_cilindros_cerrados <= 0 AND p.cilindros_abiertos <= 0), 0) AS sin_stock
            FROM tipos_producto t
            LEFT JOIN productos p ON p.tipo_id = t.id
            GROUP BY t.id, t.nombre
            ORDER BY t.id
            """
        )
    ]


def _movimientos_por_dia(filtros):
    entradas = [] if filtros.get("placa") else consultar_todos(
        """
        SELECT DATE(creado_en) AS fecha, COUNT(*) AS entradas
        FROM entradas_stock
        WHERE DATE(creado_en) BETWEEN %s AND %s
        GROUP BY DATE(creado_en)
        """,
        _parametros_fecha(filtros),
    )
    placa_sql, placa_params = _filtro_placa(filtros)
    salidas = consultar_todos(
        f"""
        SELECT DATE(creado_en) AS fecha, COUNT(*) AS salidas
        FROM salidas_stock
        WHERE DATE(creado_en) BETWEEN %s AND %s
        {placa_sql}
        GROUP BY DATE(creado_en)
        """,
        _parametros_fecha(filtros) + placa_params,
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
