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


def _lista(datos, nombre):
    if hasattr(datos, "getlist"):
        return datos.getlist(nombre)
    valor = datos.get(nombre, [])
    return valor if isinstance(valor, list) else [valor]


def listar_vehiculos():
    filas = consultar_todos(
        """
        SELECT id, placa, modelo, ultimo_uso
        FROM vehiculos_atendidos
        ORDER BY ultimo_uso DESC, placa
        """
    )
    return [dict(fila) for fila in filas]


def listar_salidas(limite=30):
    salidas = [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT s.id, s.placa, s.modelo, s.trabajador, s.creado_en,
                   COALESCE(u.nombre, 'Usuario eliminado') AS usuario,
                   COUNT(d.id) AS items,
                   COALESCE(SUM(d.cantidad_base), 0) AS total_base
            FROM salidas_stock s
            LEFT JOIN salidas_stock_detalle d ON d.salida_id = s.id
            LEFT JOIN usuarios u ON u.id = s.usuario_id
            GROUP BY s.id, s.placa, s.modelo, s.trabajador, s.creado_en, u.nombre
            ORDER BY s.id DESC
            LIMIT %s
            """,
            (limite,),
        )
    ]
    ids = [salida["id"] for salida in salidas]
    detalles = []
    if ids:
        marcadores = ", ".join(["%s"] * len(ids))
        detalles = consultar_todos(
            f"""
            SELECT d.salida_id, d.cantidad_base, d.stock_anterior, d.stock_nuevo,
                   p.nombre AS producto, p.marca, u.abreviatura
            FROM salidas_stock_detalle d
            INNER JOIN productos p ON p.id = d.producto_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            WHERE d.salida_id IN ({marcadores})
            ORDER BY d.id
            """,
            tuple(ids),
        )
    por_salida = {}
    for detalle in detalles:
        por_salida.setdefault(detalle["salida_id"], []).append(dict(detalle))
    for salida in salidas:
        salida["detalles"] = por_salida.get(salida["id"], [])
    return salidas


def resumen_salidas():
    fila = consultar_uno(
        """
        SELECT
          COUNT(*) AS total,
          COALESCE(SUM(DATE(creado_en) = CURDATE()), 0) AS hoy,
          COALESCE(SUM(YEAR(creado_en) = YEAR(CURDATE()) AND MONTH(creado_en) = MONTH(CURDATE())), 0) AS mes,
          COUNT(DISTINCT vehiculo_id) AS vehiculos
        FROM salidas_stock
        """
    )
    return {
        "total": fila["total"],
        "hoy": int(fila["hoy"]),
        "mes": int(fila["mes"]),
        "vehiculos": fila["vehiculos"],
    }


def _lineas_desde_formulario(datos):
    productos = _lista(datos, "producto_id")
    cantidades = _lista(datos, "cantidad")
    lineas = {}

    for producto_texto, cantidad_texto in zip(productos, cantidades):
        producto_id = _entero(producto_texto)
        cantidad, error = _decimal(cantidad_texto, "La cantidad")
        if not producto_id and not cantidad_texto:
            continue
        if not producto_id:
            return None, "Selecciona un producto en cada linea."
        if error:
            return None, error
        lineas[producto_id] = lineas.get(producto_id, Decimal("0.000")) + cantidad

    if not lineas:
        return None, "Agrega al menos un producto a la salida."
    return lineas, None


def registrar_salida(datos, usuario_id):
    placa = datos.get("placa", "").strip().upper()
    modelo = datos.get("modelo", "").strip() or None
    trabajador = datos.get("trabajador", "").strip()
    lineas, error = _lineas_desde_formulario(datos)

    if not placa:
        return False, "Ingresa la placa del vehiculo."
    if len(placa) > 20:
        return False, "La placa no puede superar 20 caracteres."
    if len(trabajador) < 3:
        return False, "Ingresa el trabajador que recibe los productos."
    if error:
        return False, error

    def operacion(cursor):
        cursor.execute(
            """
            SELECT id, modelo
            FROM vehiculos_atendidos
            WHERE placa = %s
            FOR UPDATE
            """,
            (placa,),
        )
        vehiculo = cursor.fetchone()
        if vehiculo:
            vehiculo_id = vehiculo["id"]
            modelo_final = modelo or vehiculo["modelo"]
            cursor.execute(
                """
                UPDATE vehiculos_atendidos
                SET modelo = %s, ultimo_uso = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (modelo_final, vehiculo_id),
            )
        else:
            cursor.execute(
                "INSERT INTO vehiculos_atendidos (placa, modelo) VALUES (%s, %s)",
                (placa, modelo),
            )
            vehiculo_id = cursor.lastrowid
            modelo_final = modelo

        cursor.execute(
            """
            INSERT INTO salidas_stock (vehiculo_id, placa, modelo, trabajador, usuario_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (vehiculo_id, placa, modelo_final, trabajador, usuario_id),
        )
        salida_id = cursor.lastrowid

        nombres = []
        for producto_id in sorted(lineas):
            cantidad = lineas[producto_id].quantize(Decimal("0.001"))
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
                return False, "Uno de los productos seleccionados no existe."
            if not producto["permite_decimal"] and cantidad != cantidad.to_integral_value():
                return False, f"{producto['nombre']} debe salir en cantidades enteras."
            if cantidad > producto["stock_actual"]:
                return False, f"No hay stock suficiente de {producto['nombre']}."

            stock_anterior = producto["stock_actual"]
            stock_nuevo = stock_anterior - cantidad
            cursor.execute("UPDATE productos SET stock_actual = %s WHERE id = %s", (stock_nuevo, producto_id))
            cursor.execute(
                """
                INSERT INTO salidas_stock_detalle
                    (salida_id, producto_id, cantidad_base, stock_anterior, stock_nuevo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (salida_id, producto_id, cantidad, stock_anterior, stock_nuevo),
            )
            motivo = f"Salida {placa} / trabajador: {trabajador}"
            cursor.execute(
                """
                INSERT INTO ajustes_stock
                    (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (producto_id, stock_anterior, stock_nuevo, -cantidad, motivo, usuario_id),
            )
            nombres.append(f"{producto['nombre']} -{cantidad} {producto['abreviatura']}")

        cursor.execute(
            """
            INSERT INTO movimientos (tipo, descripcion, usuario_id)
            VALUES (%s, %s, %s)
            """,
            ("Salida", f"{placa}: {', '.join(nombres)}", usuario_id),
        )
        return True, "Salida registrada correctamente."

    return ejecutar_transaccion(operacion)
