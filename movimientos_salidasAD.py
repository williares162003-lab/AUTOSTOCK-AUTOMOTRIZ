from decimal import Decimal, InvalidOperation

from bd import consultar_todos, consultar_uno, ejecutar_transaccion


ORIGEN_SUELTO = "suelto"
ORIGEN_BALDE_ABIERTO = "balde_abierto"
ORIGEN_CILINDRO_ABIERTO = "cilindro_abierto"


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


def _origen_texto(origen):
    return {
        ORIGEN_BALDE_ABIERTO: "Balde abierto",
        ORIGEN_CILINDRO_ABIERTO: "Cilindro abierto",
    }.get(origen, "Suelto")


def listar_vehiculos(dias_recientes=3):
    dias_recientes = max(int(dias_recientes or 3), 1)
    filas = consultar_todos(
        """
        SELECT id, placa, modelo, ultimo_uso
        FROM vehiculos_atendidos
        WHERE UPPER(placa) LIKE 'TRABAJADORES %%'
           OR UPPER(placa) = 'PARA TRABAJADORES'
           OR DATE(ultimo_uso) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY
          (UPPER(placa) LIKE 'TRABAJADORES %%' OR UPPER(placa) = 'PARA TRABAJADORES') DESC,
          ultimo_uso DESC,
          placa
        """,
        (dias_recientes - 1,),
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
            SELECT d.salida_id, d.cantidad_base, d.origen_stock,
                   d.stock_anterior, d.stock_nuevo,
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
        detalle = dict(detalle)
        detalle["origen_texto"] = _origen_texto(detalle["origen_stock"])
        por_salida.setdefault(detalle["salida_id"], []).append(detalle)
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


def renombrar_destino(origen, nuevo):
    origen = (origen or "").strip().upper()
    nuevo = (nuevo or "").strip().upper()
    if not origen or not nuevo:
        return False, "Ingresa el destino anterior y el nuevo destino.", {}
    if len(origen) > 80 or len(nuevo) > 80:
        return False, "El destino no puede superar 80 caracteres.", {}
    if origen == nuevo:
        return True, "El destino ya tiene ese nombre.", {"salidas": 0, "destinos": 0}

    def operacion(cursor):
        cursor.execute("SELECT id, modelo FROM vehiculos_atendidos WHERE placa = %s", (origen,))
        origen_fila = cursor.fetchone()
        cursor.execute("SELECT id, modelo FROM vehiculos_atendidos WHERE placa = %s", (nuevo,))
        nuevo_fila = cursor.fetchone()
        origen_id = origen_fila["id"] if origen_fila else None
        destino_id = nuevo_fila["id"] if nuevo_fila else None
        destinos_modificados = 0
        cursor.execute("SELECT COUNT(*) AS total FROM salidas_stock WHERE placa = %s", (origen,))
        salidas_origen = cursor.fetchone()["total"]
        if not origen_id and salidas_origen == 0:
            return {"salidas": 0, "destinos": 0}

        if destino_id and origen_id and destino_id != origen_id:
            cursor.execute(
                """
                UPDATE salidas_stock
                SET vehiculo_id = %s, placa = %s
                WHERE placa = %s OR vehiculo_id = %s
                """,
                (destino_id, nuevo, origen, origen_id),
            )
            salidas_modificadas = cursor.rowcount
            if not nuevo_fila.get("modelo") and origen_fila.get("modelo"):
                cursor.execute(
                    "UPDATE vehiculos_atendidos SET modelo = %s WHERE id = %s",
                    (origen_fila["modelo"], destino_id),
                )
            cursor.execute("DELETE FROM vehiculos_atendidos WHERE id = %s", (origen_id,))
            destinos_modificados = 1
            return {"salidas": salidas_modificadas, "destinos": destinos_modificados}

        if not destino_id:
            if origen_id:
                cursor.execute("UPDATE vehiculos_atendidos SET placa = %s WHERE id = %s", (nuevo, origen_id))
                destino_id = origen_id
                destinos_modificados = cursor.rowcount
            else:
                cursor.execute("INSERT INTO vehiculos_atendidos (placa, modelo) VALUES (%s, NULL)", (nuevo,))
                destino_id = cursor.lastrowid
                destinos_modificados = 1

        if origen_id:
            cursor.execute(
                """
                UPDATE salidas_stock
                SET vehiculo_id = %s, placa = %s
                WHERE placa = %s OR vehiculo_id = %s
                """,
                (destino_id, nuevo, origen, origen_id),
            )
        else:
            cursor.execute(
                "UPDATE salidas_stock SET vehiculo_id = %s, placa = %s WHERE placa = %s",
                (destino_id, nuevo, origen),
            )
        return {"salidas": cursor.rowcount, "destinos": destinos_modificados}

    resultado = ejecutar_transaccion(operacion)
    return True, "Destino actualizado correctamente.", resultado


def _lineas_desde_formulario(datos):
    productos = _lista(datos, "producto_id")
    cantidades = _lista(datos, "cantidad")
    origenes = _lista(datos, "origen_stock")
    lineas = {}

    if len(origenes) < len(productos):
        origenes.extend([ORIGEN_SUELTO] * (len(productos) - len(origenes)))

    for producto_texto, cantidad_texto, origen in zip(productos, cantidades, origenes):
        producto_id = _entero(producto_texto)
        cantidad, error = _decimal(cantidad_texto, "La cantidad")
        if not producto_id and not cantidad_texto:
            continue
        if not producto_id:
            return None, "Selecciona un producto en cada linea."
        if origen not in (ORIGEN_SUELTO, ORIGEN_BALDE_ABIERTO, ORIGEN_CILINDRO_ABIERTO):
            return None, "Selecciona un origen de stock valido."
        if error:
            return None, error
        clave = (producto_id, origen)
        lineas[clave] = lineas.get(clave, Decimal("0.000")) + cantidad

    if not lineas:
        return None, "Agrega al menos un producto a la salida."
    return lineas, None


def registrar_salida(datos, usuario_id):
    placa = datos.get("placa", "").strip().upper()
    modelo = datos.get("modelo", "").strip() or None
    trabajador = datos.get("trabajador", "").strip()
    lineas, error = _lineas_desde_formulario(datos)

    if not placa:
        return False, "Ingresa el destino de la salida."
    if len(placa) > 80:
        return False, "El destino no puede superar 80 caracteres."
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
        for producto_id, origen in sorted(lineas):
            cantidad = lineas[(producto_id, origen)].quantize(Decimal("0.001"))
            cursor.execute(
                """
                SELECT p.id, p.nombre, p.stock_actual, p.stock_suelto,
                       p.stock_balde_abierto, p.baldes_abiertos, p.stock_baldes_cerrados,
                       p.stock_cilindro_abierto, p.cilindros_abiertos,
                       p.stock_cilindros_cerrados, p.litros_por_cilindro,
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
                return False, "Uno de los productos seleccionados no existe."
            if not producto["permite_decimal"] and cantidad != cantidad.to_integral_value():
                return False, f"{producto['nombre']} debe salir en cantidades enteras."

            disponible = producto["stock_suelto"]
            if origen == ORIGEN_BALDE_ABIERTO and producto["baldes_abiertos"] <= 0:
                return False, f"No hay balde abierto en uso para {producto['nombre']}."
            if origen == ORIGEN_CILINDRO_ABIERTO and producto["cilindros_abiertos"] <= 0:
                return False, f"No hay cilindro abierto en uso para {producto['nombre']}."
            if (
                origen == ORIGEN_CILINDRO_ABIERTO
                and producto["stock_cilindro_abierto"] + cantidad > producto["litros_por_cilindro"]
            ):
                disponible_cilindro = producto["litros_por_cilindro"] - producto["stock_cilindro_abierto"]
                return False, (
                    f"No hay litros suficientes en el cilindro abierto de {producto['nombre']}. "
                    f"Disponible: {disponible_cilindro} {producto['abreviatura']}."
                )
            if origen == ORIGEN_SUELTO and cantidad > disponible:
                return False, f"No hay stock suficiente de {producto['nombre']} en {_origen_texto(origen).lower()}."

            stock_anterior = producto["stock_actual"]
            stock_suelto_nuevo = producto["stock_suelto"]
            stock_balde_abierto_nuevo = producto["stock_balde_abierto"]
            stock_cilindro_abierto_nuevo = producto["stock_cilindro_abierto"]
            if origen == ORIGEN_BALDE_ABIERTO:
                stock_balde_abierto_nuevo += cantidad
            elif origen == ORIGEN_CILINDRO_ABIERTO:
                stock_cilindro_abierto_nuevo += cantidad
            else:
                stock_suelto_nuevo -= cantidad
            stock_nuevo = stock_suelto_nuevo
            cursor.execute(
                """
                UPDATE productos
                SET stock_suelto = %s,
                    stock_balde_abierto = %s,
                    stock_cilindro_abierto = %s,
                    stock_actual = %s
                WHERE id = %s
                """,
                (
                    stock_suelto_nuevo,
                    stock_balde_abierto_nuevo,
                    stock_cilindro_abierto_nuevo,
                    stock_nuevo,
                    producto_id,
                ),
            )
            cursor.execute(
                """
                INSERT INTO salidas_stock_detalle
                    (salida_id, producto_id, cantidad_base, origen_stock, stock_anterior, stock_nuevo)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (salida_id, producto_id, cantidad, origen, stock_anterior, stock_nuevo),
            )
            motivo = f"Salida {placa} / trabajador: {trabajador} / {_origen_texto(origen)}"
            diferencia = (
                Decimal("0.000")
                if origen in (ORIGEN_BALDE_ABIERTO, ORIGEN_CILINDRO_ABIERTO)
                else -cantidad
            )
            cursor.execute(
                """
                INSERT INTO ajustes_stock
                    (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id),
            )
            nombres.append(
                f"{producto['nombre']} -{cantidad} {producto['abreviatura']} ({_origen_texto(origen)})"
            )

        cursor.execute(
            """
            INSERT INTO movimientos (tipo, descripcion, usuario_id)
            VALUES (%s, %s, %s)
            """,
            ("Salida", f"{placa}: {', '.join(nombres)}", usuario_id),
        )
        return True, "Salida registrada correctamente."

    return ejecutar_transaccion(operacion)
