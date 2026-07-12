from decimal import Decimal, InvalidOperation

from bd import consultar_todos, consultar_uno, ejecutar_transaccion


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _decimal(valor, nombre):
    try:
        numero = Decimal(str(valor or "0").replace(",", "."))
    except InvalidOperation:
        return None, f"{nombre} debe ser un numero valido."
    if numero <= 0:
        return None, f"{nombre} debe ser mayor que cero."
    return numero.quantize(Decimal("0.001")), None


def listar_entradas(limite=30):
    filas = consultar_todos(
        """
        SELECT e.id, e.cantidad, e.cantidad_base, e.presentacion_nombre,
               e.stock_anterior, e.stock_nuevo, e.proveedor, e.documento,
               e.motivo, e.creado_en, p.nombre AS producto, p.marca,
               u.abreviatura, COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM entradas_stock e
        INNER JOIN productos p ON p.id = e.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = e.usuario_id
        ORDER BY e.id DESC
        LIMIT %s
        """,
        (limite,),
    )
    return [dict(fila) for fila in filas]


def resumen_entradas():
    fila = consultar_uno(
        """
        SELECT
          COUNT(*) AS total,
          COALESCE(SUM(DATE(creado_en) = CURDATE()), 0) AS hoy,
          COALESCE(SUM(YEAR(creado_en) = YEAR(CURDATE()) AND MONTH(creado_en) = MONTH(CURDATE())), 0) AS mes,
          COUNT(DISTINCT producto_id) AS productos
        FROM entradas_stock
        """
    )
    return {
        "total": fila["total"],
        "hoy": int(fila["hoy"]),
        "mes": int(fila["mes"]),
        "productos": fila["productos"],
    }


def registrar_entrada(datos, usuario_id):
    producto_id = _entero(datos.get("producto_id"))
    presentacion_id = datos.get("presentacion_id", "base")
    cantidad, error = _decimal(datos.get("cantidad"), "La cantidad")
    proveedor = datos.get("proveedor", "").strip() or None
    documento = datos.get("documento", "").strip() or None
    motivo = datos.get("motivo", "").strip() or "Entrada de almacen"

    if error:
        return False, error
    if not producto_id:
        return False, "Selecciona un producto."
    if len(motivo) < 3:
        return False, "Ingresa un motivo valido."

    def operacion(cursor):
        cursor.execute(
            """
            SELECT p.id, p.nombre, p.stock_actual, u.abreviatura, u.permite_decimal
            FROM productos p
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            WHERE p.id = %s
            FOR UPDATE
            """,
            (producto_id,),
        )
        producto = cursor.fetchone()
        if not producto:
            return False, "El producto seleccionado no existe."

        factor = Decimal("1.000")
        presentacion_nombre = "Unidad base"
        presentacion_bd_id = None
        if presentacion_id and presentacion_id != "base":
            presentacion_bd_id = _entero(presentacion_id)
            if not presentacion_bd_id:
                return False, "La presentacion seleccionada no es valida."
            cursor.execute(
                """
                SELECT id, nombre, factor
                FROM presentaciones_producto
                WHERE id = %s AND producto_id = %s
                """,
                (presentacion_bd_id, producto_id),
            )
            presentacion = cursor.fetchone()
            if not presentacion:
                return False, "La presentacion no pertenece al producto seleccionado."
            factor = presentacion["factor"]
            presentacion_nombre = presentacion["nombre"]

        cantidad_base = (cantidad * factor).quantize(Decimal("0.001"))
        if not producto["permite_decimal"] and cantidad_base != cantidad_base.to_integral_value():
            return False, "La entrada debe resultar en una cantidad entera para este producto."

        stock_anterior = producto["stock_actual"]
        stock_nuevo = stock_anterior + cantidad_base
        cursor.execute("UPDATE productos SET stock_actual = %s WHERE id = %s", (stock_nuevo, producto_id))
        cursor.execute(
            """
            INSERT INTO entradas_stock
                (producto_id, presentacion_id, presentacion_nombre, factor, cantidad,
                 cantidad_base, stock_anterior, stock_nuevo, proveedor, documento, motivo, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                producto_id,
                presentacion_bd_id,
                presentacion_nombre,
                factor,
                cantidad,
                cantidad_base,
                stock_anterior,
                stock_nuevo,
                proveedor,
                documento,
                motivo,
                usuario_id,
            ),
        )
        detalle = f"Entrada: {motivo}"
        if proveedor:
            detalle += f" / {proveedor}"
        if documento:
            detalle += f" / {documento}"
        cursor.execute(
            """
            INSERT INTO ajustes_stock
                (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (producto_id, stock_anterior, stock_nuevo, cantidad_base, detalle, usuario_id),
        )
        cursor.execute(
            """
            INSERT INTO movimientos (tipo, descripcion, usuario_id)
            VALUES (%s, %s, %s)
            """,
            (
                "Entrada",
                f"{producto['nombre']}: +{cantidad_base} {producto['abreviatura']}",
                usuario_id,
            ),
        )
        return True, "Entrada registrada correctamente."

    return ejecutar_transaccion(operacion)
