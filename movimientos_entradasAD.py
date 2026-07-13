from decimal import Decimal, InvalidOperation

from bd import consultar_todos, consultar_uno, ejecutar_transaccion


ORIGEN_SUELTO = "suelto"
ORIGEN_BALDE_CERRADO = "balde_cerrado"


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


def _origen_texto(origen):
    return {
        ORIGEN_SUELTO: "Stock suelto",
        ORIGEN_BALDE_CERRADO: "Balde cerrado",
    }.get(origen, "Stock suelto")


def listar_entradas(limite=30):
    filas = consultar_todos(
        """
        SELECT e.id, e.cantidad, e.cantidad_base, e.origen_stock, e.presentacion_nombre,
               e.stock_anterior, e.stock_nuevo, e.documento,
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
    entradas = []
    for fila in filas:
        entrada = dict(fila)
        entrada["origen_texto"] = _origen_texto(entrada["origen_stock"])
        entradas.append(entrada)
    return entradas


def listar_aperturas_balde(limite=12):
    filas = consultar_todos(
        """
        SELECT a.id, a.tipo, a.baldes_abiertos, a.contenido_por_balde, a.cantidad_base,
               a.stock_baldes_anterior, a.stock_baldes_nuevo,
               a.baldes_en_uso_anterior, a.baldes_en_uso_nuevo,
               a.stock_abierto_anterior, a.stock_abierto_nuevo,
               a.creado_en, p.nombre AS producto, p.marca, u.abreviatura,
               COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM aperturas_balde a
        INNER JOIN productos p ON p.id = a.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = a.usuario_id
        ORDER BY a.id DESC
        LIMIT %s
        """,
        (limite,),
    )
    aperturas = []
    for fila in filas:
        apertura = dict(fila)
        apertura["tipo_texto"] = "Terminado" if apertura["tipo"] == "cierre" else "Abierto"
        aperturas.append(apertura)
    return aperturas


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
    tipo_entrada = datos.get("tipo_entrada", ORIGEN_SUELTO)
    presentacion_id = datos.get("presentacion_id", "base")
    cantidad, error = _decimal(datos.get("cantidad"), "La cantidad")
    documento = datos.get("documento", "").strip() or None
    motivo = datos.get("motivo", "").strip() or "Entrada de almacen"

    if tipo_entrada not in (ORIGEN_SUELTO, ORIGEN_BALDE_CERRADO):
        return False, "Selecciona un tipo de entrada valido."
    if error:
        return False, error
    if not producto_id:
        return False, "Selecciona un producto."
    if len(motivo) < 3:
        return False, "Ingresa un motivo valido."
    if tipo_entrada == ORIGEN_BALDE_CERRADO and cantidad != cantidad.to_integral_value():
        return False, "La cantidad de baldes debe ser entera."

    def operacion(cursor):
        cursor.execute(
            """
            SELECT p.id, p.nombre, p.stock_actual, p.stock_suelto,
                   p.stock_balde_abierto, p.baldes_abiertos, p.stock_baldes_cerrados,
                   u.abreviatura, u.permite_decimal
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
        cantidad_base = cantidad

        if tipo_entrada == ORIGEN_SUELTO:
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
            stock_suelto_nuevo = producto["stock_suelto"] + cantidad_base
            stock_nuevo = stock_suelto_nuevo
            cursor.execute(
                """
                UPDATE productos
                SET stock_suelto = %s, stock_actual = %s
                WHERE id = %s
                """,
                (stock_suelto_nuevo, stock_nuevo, producto_id),
            )
            diferencia_ajuste = cantidad_base
            descripcion_movimiento = f"{producto['nombre']}: +{cantidad_base} {producto['abreviatura']}"
        else:
            cantidad_base = Decimal("0.000")
            presentacion_nombre = "Balde cerrado"
            stock_anterior = producto["stock_actual"]
            stock_nuevo = stock_anterior
            stock_baldes_nuevo = producto["stock_baldes_cerrados"] + cantidad
            cursor.execute(
                """
                UPDATE productos
                SET stock_baldes_cerrados = %s
                WHERE id = %s
                """,
                (stock_baldes_nuevo, producto_id),
            )
            diferencia_ajuste = Decimal("0.000")
            descripcion_movimiento = f"{producto['nombre']}: +{cantidad} balde(s) cerrados"

        cursor.execute(
            """
            INSERT INTO entradas_stock
                (producto_id, presentacion_id, presentacion_nombre, factor, cantidad,
                 cantidad_base, origen_stock, stock_anterior, stock_nuevo,
                 documento, motivo, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                producto_id,
                presentacion_bd_id,
                presentacion_nombre,
                factor,
                cantidad,
                cantidad_base,
                tipo_entrada,
                stock_anterior,
                stock_nuevo,
                documento,
                motivo,
                usuario_id,
            ),
        )
        detalle = f"Entrada: {motivo}"
        if documento:
            detalle += f" / {documento}"
        if tipo_entrada == ORIGEN_BALDE_CERRADO:
            detalle += f" / {cantidad} balde(s) cerrados"
        cursor.execute(
            """
            INSERT INTO ajustes_stock
                (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (producto_id, stock_anterior, stock_nuevo, diferencia_ajuste, detalle, usuario_id),
        )
        cursor.execute(
            """
            INSERT INTO movimientos (tipo, descripcion, usuario_id)
            VALUES (%s, %s, %s)
            """,
            ("Entrada", descripcion_movimiento, usuario_id),
        )
        return True, "Entrada registrada correctamente."

    return ejecutar_transaccion(operacion)


def abrir_balde(datos, usuario_id):
    producto_id = _entero(datos.get("producto_id"))
    baldes = Decimal("1.000")

    if not producto_id:
        return False, "Selecciona un producto."

    def operacion(cursor):
        cursor.execute(
            """
            SELECT p.id, p.nombre, p.stock_actual, p.stock_suelto,
                   p.stock_balde_abierto, p.baldes_abiertos, p.stock_baldes_cerrados,
                   u.abreviatura
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
        if producto["baldes_abiertos"] > 0:
            return False, "Primero marca como terminado el balde abierto de este producto."
        if producto["stock_baldes_cerrados"] < baldes:
            return False, "No hay baldes cerrados disponibles para abrir."

        stock_baldes_nuevo = producto["stock_baldes_cerrados"] - baldes
        baldes_en_uso_nuevo = producto["baldes_abiertos"] + baldes
        cursor.execute(
            """
            UPDATE productos
            SET stock_baldes_cerrados = %s,
                baldes_abiertos = %s,
                stock_balde_abierto = 0,
                stock_actual = stock_suelto
            WHERE id = %s
            """,
            (stock_baldes_nuevo, baldes_en_uso_nuevo, producto_id),
        )
        cursor.execute(
            """
            INSERT INTO aperturas_balde
                (producto_id, tipo, baldes_abiertos, contenido_por_balde, cantidad_base,
                 stock_baldes_anterior, stock_baldes_nuevo,
                 baldes_en_uso_anterior, baldes_en_uso_nuevo,
                 stock_abierto_anterior, stock_abierto_nuevo,
                 stock_anterior, stock_nuevo, usuario_id)
            VALUES (%s, 'apertura', %s, 0, 0, %s, %s, %s, %s, %s, 0, %s, %s, %s)
            """,
            (
                producto_id,
                baldes,
                producto["stock_baldes_cerrados"],
                stock_baldes_nuevo,
                producto["baldes_abiertos"],
                baldes_en_uso_nuevo,
                producto["stock_balde_abierto"],
                producto["stock_actual"],
                producto["stock_suelto"],
                usuario_id,
            ),
        )
        cursor.execute(
            """
            INSERT INTO ajustes_stock
                (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
            VALUES (%s, %s, %s, 0, %s, %s)
            """,
            (
                producto_id,
                producto["stock_actual"],
                producto["stock_suelto"],
                "Balde abierto para consumo por salidas",
                usuario_id,
            ),
        )
        cursor.execute(
            """
            INSERT INTO movimientos (tipo, descripcion, usuario_id)
            VALUES (%s, %s, %s)
            """,
            ("Apertura", f"{producto['nombre']}: 1 balde abierto", usuario_id),
        )
        return True, "Balde abierto. Ahora registra las salidas reales desde ese balde."

    return ejecutar_transaccion(operacion)


def cerrar_balde(datos, usuario_id):
    producto_id = _entero(datos.get("producto_id"))
    if not producto_id:
        return False, "Selecciona un producto."

    def operacion(cursor):
        cursor.execute(
            """
            SELECT p.id, p.nombre, p.stock_actual, p.stock_suelto,
                   p.stock_balde_abierto, p.baldes_abiertos, p.stock_baldes_cerrados,
                   u.abreviatura
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
        if producto["baldes_abiertos"] <= 0:
            return False, "Este producto no tiene balde abierto en uso."

        baldes_en_uso_nuevo = producto["baldes_abiertos"] - Decimal("1.000")
        cursor.execute(
            """
            UPDATE productos
            SET baldes_abiertos = %s,
                stock_balde_abierto = 0,
                stock_actual = stock_suelto
            WHERE id = %s
            """,
            (baldes_en_uso_nuevo, producto_id),
        )
        cursor.execute(
            """
            INSERT INTO aperturas_balde
                (producto_id, tipo, baldes_abiertos, contenido_por_balde, cantidad_base,
                 stock_baldes_anterior, stock_baldes_nuevo,
                 baldes_en_uso_anterior, baldes_en_uso_nuevo,
                 stock_abierto_anterior, stock_abierto_nuevo,
                 stock_anterior, stock_nuevo, usuario_id)
            VALUES (%s, 'cierre', 1, 0, 0, %s, %s, %s, %s, %s, 0, %s, %s, %s)
            """,
            (
                producto_id,
                producto["stock_baldes_cerrados"],
                producto["stock_baldes_cerrados"],
                producto["baldes_abiertos"],
                baldes_en_uso_nuevo,
                producto["stock_balde_abierto"],
                producto["stock_actual"],
                producto["stock_suelto"],
                usuario_id,
            ),
        )
        motivo = f"Balde terminado. Consumo registrado: {producto['stock_balde_abierto']} {producto['abreviatura']}"
        cursor.execute(
            """
            INSERT INTO ajustes_stock
                (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
            VALUES (%s, %s, %s, 0, %s, %s)
            """,
            (producto_id, producto["stock_actual"], producto["stock_suelto"], motivo, usuario_id),
        )
        cursor.execute(
            """
            INSERT INTO movimientos (tipo, descripcion, usuario_id)
            VALUES (%s, %s, %s)
            """,
            ("Cierre", f"{producto['nombre']}: balde terminado", usuario_id),
        )
        return True, "Balde marcado como terminado."

    return ejecutar_transaccion(operacion)
