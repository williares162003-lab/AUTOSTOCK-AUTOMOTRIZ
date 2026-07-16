import logging
from datetime import datetime

from bd import consultar_todos, consultar_uno


logger = logging.getLogger(__name__)


def _fecha_valida(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _placa_valida(valor):
    return (valor or "").strip().upper()[:80]


def _origen_texto(origen):
    return {
        "suelto": "Stock suelto",
        "balde_abierto": "Balde abierto",
        "balde_cerrado": "Balde cerrado",
        "cilindro_abierto": "Cilindro abierto",
        "cilindro_cerrado": "Cilindro cerrado",
        "caja_cerrada": "Caja cerrada",
    }.get(origen, "Stock suelto")


def _es_galon(abreviatura):
    return "gal" in (abreviatura or "").lower()


def _unidad_producto(abreviatura):
    return "L" if _es_galon(abreviatura) else abreviatura


def _aplicar_filtros(
    base,
    parametros,
    columna_fecha,
    producto_id,
    fecha_inicio,
    fecha_fin,
    columna_producto,
    area_id=None,
    tipo_id=None,
    categoria_id=None,
    alias_producto="p",
):
    filtros = []
    if producto_id:
        filtros.append(f"{columna_producto} = %s")
        parametros.append(producto_id)
    if area_id:
        filtros.append(f"{alias_producto}.tipo_id IN (SELECT id FROM tipos_producto WHERE area_id = %s)")
        parametros.append(area_id)
    if tipo_id:
        filtros.append(f"{alias_producto}.tipo_id = %s")
        parametros.append(tipo_id)
    if categoria_id:
        filtros.append(f"{alias_producto}.categoria_id = %s")
        parametros.append(categoria_id)
    if fecha_inicio:
        filtros.append(f"DATE({columna_fecha}) >= %s")
        parametros.append(fecha_inicio)
    if fecha_fin:
        filtros.append(f"DATE({columna_fecha}) <= %s")
        parametros.append(fecha_fin)
    if filtros:
        base += " WHERE " + " AND ".join(filtros)
    return base


def obtener_producto_kardex(producto_id):
    if not producto_id:
        return None
    producto = consultar_uno(
        """
        SELECT p.id, p.nombre, p.marca, p.stock_actual, p.stock_suelto,
               p.stock_balde_abierto, p.baldes_abiertos, p.stock_baldes_cerrados,
               p.stock_cilindro_abierto, p.cilindros_abiertos, p.stock_cilindros_cerrados,
               p.litros_por_cilindro, p.stock_cajas_cerradas, p.unidades_por_caja,
               p.stock_minimo, t.nombre AS tipo, c.nombre AS categoria,
               u.nombre AS unidad, u.abreviatura
        FROM productos p
        INNER JOIN tipos_producto t ON t.id = p.tipo_id
        INNER JOIN categorias c ON c.id = p.categoria_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        WHERE p.id = %s
        """,
        (producto_id,),
    )
    if producto:
        producto = dict(producto)
        producto["abreviatura"] = _unidad_producto(producto["abreviatura"])
    return producto


def _entradas(producto_id, fecha_inicio, fecha_fin, area_id=None, tipo_id=None, categoria_id=None):
    parametros = []
    sql = """
        SELECT e.id, e.producto_id, e.creado_en AS fecha, e.origen_stock,
               e.cantidad, e.cantidad_base, e.presentacion_nombre,
               e.stock_anterior, e.stock_nuevo, e.documento, e.motivo,
               p.nombre AS producto, p.marca, u.abreviatura,
               COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM entradas_stock e
        INNER JOIN productos p ON p.id = e.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = e.usuario_id
    """
    sql = _aplicar_filtros(
        sql,
        parametros,
        "e.creado_en",
        producto_id,
        fecha_inicio,
        fecha_fin,
        "e.producto_id",
        area_id,
        tipo_id,
        categoria_id,
    )
    filas = consultar_todos(sql, tuple(parametros))
    movimientos = []
    for fila in filas:
        es_balde = fila["origen_stock"] == "balde_cerrado"
        es_cilindro = fila["origen_stock"] == "cilindro_cerrado"
        es_caja = fila["origen_stock"] == "caja_cerrada"
        movimientos.append(
            {
                "fecha": fila["fecha"],
                "producto_id": fila["producto_id"],
                "producto": fila["producto"],
                "marca": fila["marca"],
                "tipo": "Entrada",
                "tipo_clase": "entrada",
                "origen": _origen_texto(fila["origen_stock"]),
                "detalle": fila["motivo"] or "Entrada de almacen",
                "referencia": fila["documento"] or "-",
                "entrada": fila["cantidad"] if es_balde or es_cilindro or es_caja else fila["cantidad_base"],
                "salida": None,
                "unidad": (
                    "balde(s)" if es_balde
                    else ("cilindro(s)" if es_cilindro else ("caja(s)" if es_caja else _unidad_producto(fila["abreviatura"])))
                ),
                "stock_anterior": fila["stock_anterior"],
                "stock_nuevo": fila["stock_nuevo"],
                "usuario": fila["usuario"],
            }
        )
    return movimientos


def _salidas(producto_id, fecha_inicio, fecha_fin, area_id=None, tipo_id=None, categoria_id=None):
    return _salidas_filtradas(producto_id, fecha_inicio, fecha_fin, "", area_id, tipo_id, categoria_id)


def _salidas_filtradas(producto_id, fecha_inicio, fecha_fin, placa, area_id=None, tipo_id=None, categoria_id=None):
    parametros = []
    sql = """
        SELECT d.id, d.producto_id, d.cantidad_base, d.origen_stock,
               d.stock_anterior, d.stock_nuevo, s.creado_en AS fecha,
               s.placa, s.modelo, s.trabajador,
               p.nombre AS producto, p.marca, u.abreviatura,
               COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM salidas_stock_detalle d
        INNER JOIN salidas_stock s ON s.id = d.salida_id
        INNER JOIN productos p ON p.id = d.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = s.usuario_id
    """
    sql = _aplicar_filtros(
        sql,
        parametros,
        "s.creado_en",
        producto_id,
        fecha_inicio,
        fecha_fin,
        "d.producto_id",
        area_id,
        tipo_id,
        categoria_id,
    )
    sql += (" AND " if " WHERE " in sql else " WHERE ") + "COALESCE(s.estado, 'activa') = 'activa'"
    if placa:
        sql += (
            " AND " if " WHERE " in sql else " WHERE "
        ) + """
        (
            UPPER(s.placa) LIKE %s
            OR UPPER(COALESCE(s.modelo, '')) LIKE %s
        )
        """
        busqueda = f"%{placa}%"
        parametros.extend([busqueda, busqueda])
    filas = consultar_todos(sql, tuple(parametros))
    movimientos = []
    for fila in filas:
        detalle = f"{fila['placa']} / {fila['trabajador']}"
        if fila["modelo"]:
            detalle += f" / {fila['modelo']}"
        movimientos.append(
            {
                "fecha": fila["fecha"],
                "producto_id": fila["producto_id"],
                "producto": fila["producto"],
                "marca": fila["marca"],
                "tipo": "Salida",
                "tipo_clase": "salida",
                "origen": _origen_texto(fila["origen_stock"]),
                "detalle": detalle,
                "referencia": fila["placa"],
                "entrada": None,
                "salida": fila["cantidad_base"],
                "unidad": _unidad_producto(fila["abreviatura"]),
                "stock_anterior": fila["stock_anterior"],
                "stock_nuevo": fila["stock_nuevo"],
                "usuario": fila["usuario"],
            }
        )
    return movimientos


def _ajustes(producto_id, fecha_inicio, fecha_fin, area_id=None, tipo_id=None, categoria_id=None):
    parametros = []
    sql = """
        SELECT a.id, a.producto_id, a.creado_en AS fecha, a.stock_anterior,
               a.stock_nuevo, a.diferencia, a.motivo,
               p.nombre AS producto, p.marca, u.abreviatura,
               COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM ajustes_stock a
        INNER JOIN productos p ON p.id = a.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = a.usuario_id
    """
    sql = _aplicar_filtros(
        sql,
        parametros,
        "a.creado_en",
        producto_id,
        fecha_inicio,
        fecha_fin,
        "a.producto_id",
        area_id,
        tipo_id,
        categoria_id,
    )
    if " WHERE " in sql:
        sql += """
          AND a.motivo NOT LIKE 'Entrada:%%'
          AND a.motivo NOT LIKE 'Salida %%'
          AND a.motivo NOT LIKE 'Balde abierto%%'
          AND a.motivo NOT LIKE 'Balde terminado%%'
          AND a.motivo NOT LIKE 'Cilindro abierto%%'
          AND a.motivo NOT LIKE 'Cilindro terminado%%'
          AND a.motivo NOT LIKE 'Caja abierta%%'
        """
    else:
        sql += """
        WHERE a.motivo NOT LIKE 'Entrada:%%'
          AND a.motivo NOT LIKE 'Salida %%'
          AND a.motivo NOT LIKE 'Balde abierto%%'
          AND a.motivo NOT LIKE 'Balde terminado%%'
          AND a.motivo NOT LIKE 'Cilindro abierto%%'
          AND a.motivo NOT LIKE 'Cilindro terminado%%'
          AND a.motivo NOT LIKE 'Caja abierta%%'
        """
    filas = consultar_todos(sql, tuple(parametros))
    movimientos = []
    for fila in filas:
        diferencia = fila["diferencia"]
        movimientos.append(
            {
                "fecha": fila["fecha"],
                "producto_id": fila["producto_id"],
                "producto": fila["producto"],
                "marca": fila["marca"],
                "tipo": "Ajuste",
                "tipo_clase": "ajuste",
                "origen": "Ajuste manual",
                "detalle": fila["motivo"],
                "referencia": "-",
                "entrada": diferencia if diferencia > 0 else None,
                "salida": abs(diferencia) if diferencia < 0 else None,
                "unidad": _unidad_producto(fila["abreviatura"]),
                "stock_anterior": fila["stock_anterior"],
                "stock_nuevo": fila["stock_nuevo"],
                "usuario": fila["usuario"],
            }
        )
    return movimientos


def _baldes(producto_id, fecha_inicio, fecha_fin, area_id=None, tipo_id=None, categoria_id=None):
    parametros = []
    sql = """
        SELECT a.id, a.producto_id, a.envase, a.tipo, a.baldes_abiertos, a.cantidad_base,
               a.stock_baldes_anterior, a.stock_baldes_nuevo,
               a.baldes_en_uso_anterior, a.baldes_en_uso_nuevo,
               a.stock_abierto_anterior, a.stock_abierto_nuevo, a.contenido_por_balde,
               a.stock_anterior, a.stock_nuevo, a.creado_en AS fecha,
               p.nombre AS producto, p.marca, u.abreviatura,
               COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM aperturas_balde a
        INNER JOIN productos p ON p.id = a.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = a.usuario_id
    """
    sql = _aplicar_filtros(
        sql,
        parametros,
        "a.creado_en",
        producto_id,
        fecha_inicio,
        fecha_fin,
        "a.producto_id",
        area_id,
        tipo_id,
        categoria_id,
    )
    filas = consultar_todos(sql, tuple(parametros))
    movimientos = []
    for fila in filas:
        es_cierre = fila["tipo"] == "cierre"
        es_cilindro = fila["envase"] == "cilindro"
        es_caja = fila["envase"] == "caja"
        envase = "Caja" if es_caja else ("Cilindro" if es_cilindro else "Balde")
        unidad_envase = "caja(s)" if es_caja else ("cilindro(s)" if es_cilindro else "balde(s)")
        unidad_producto = _unidad_producto(fila["abreviatura"])
        movimientos.append(
            {
                "fecha": fila["fecha"],
                "producto_id": fila["producto_id"],
                "producto": fila["producto"],
                "marca": fila["marca"],
                "tipo": (
                    "Caja terminada" if es_cierre and es_caja
                    else ("Caja abierta" if es_caja else (f"{envase} terminado" if es_cierre else f"{envase} abierto"))
                ),
                "tipo_clase": "balde",
                "origen": "Control de envases",
                "detalle": (
                    f"Consumo registrado: {fila['stock_abierto_anterior']} {unidad_producto}"
                    if es_cierre
                    else f"Se abre 1 {envase.lower()} para registrar salidas reales"
                ),
                "referencia": (
                    f"Cerrados {fila['stock_baldes_anterior']} -> {fila['stock_baldes_nuevo']}"
                    + (
                        f" / Capacidad {fila['contenido_por_balde']} {unidad_producto}"
                        if es_cilindro or es_caja
                        else ""
                    )
                ),
                "entrada": None,
                "salida": fila["baldes_abiertos"] if not es_cierre else None,
                "unidad": unidad_envase,
                "stock_anterior": fila["stock_anterior"],
                "stock_nuevo": fila["stock_nuevo"],
                "usuario": fila["usuario"],
            }
        )
    return movimientos


def listar_movimientos_kardex(filtros):
    movimientos, errores = listar_movimientos_kardex_con_errores(filtros)
    if errores:
        raise RuntimeError("; ".join(error["detalle"] for error in errores))
    return movimientos


def listar_movimientos_kardex_con_errores(filtros):
    producto_id = _entero(filtros.get("producto_id"))
    area_id = _entero(filtros.get("area_id"))
    tipo_id = _entero(filtros.get("tipo_id"))
    categoria_id = _entero(filtros.get("categoria_id"))
    fecha_inicio = _fecha_valida(filtros.get("fecha_inicio"))
    fecha_fin = _fecha_valida(filtros.get("fecha_fin"))
    tipo = filtros.get("tipo", "")
    placa = _placa_valida(filtros.get("placa", ""))

    movimientos = []
    errores = []
    consultas = (
        ("entrada", "entradas", _entradas),
        (
            "salida",
            "salidas",
            lambda producto, inicio, fin, area, tipo_producto, categoria: _salidas_filtradas(
                producto,
                inicio,
                fin,
                placa,
                area,
                tipo_producto,
                categoria,
            ),
        ),
        ("ajuste", "ajustes", _ajustes),
        ("balde", "baldes", _baldes),
    )
    for clave, etiqueta, consulta in consultas:
        if placa and clave != "salida":
            continue
        if tipo not in ("", clave):
            continue
        try:
            movimientos.extend(consulta(producto_id, fecha_inicio, fecha_fin, area_id, tipo_id, categoria_id))
        except Exception as error:
            logger.exception("No se pudo cargar kardex de %s", etiqueta)
            errores.append(
                {
                    "tipo": clave,
                    "mensaje": f"No se pudo leer {etiqueta}.",
                    "detalle": str(error),
                }
            )

    movimientos.sort(key=lambda item: item["fecha"] or datetime.min, reverse=True)
    return movimientos[:250], errores


def resumen_kardex(movimientos):
    return {
        "total": len(movimientos),
        "entradas": sum(1 for movimiento in movimientos if movimiento["tipo_clase"] == "entrada"),
        "salidas": sum(1 for movimiento in movimientos if movimiento["tipo_clase"] == "salida"),
        "ajustes": sum(1 for movimiento in movimientos if movimiento["tipo_clase"] == "ajuste"),
        "baldes": sum(1 for movimiento in movimientos if movimiento["tipo_clase"] == "balde"),
    }
