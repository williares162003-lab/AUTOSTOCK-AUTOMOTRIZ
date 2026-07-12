from decimal import Decimal, InvalidOperation

from bd import consultar_todos, consultar_uno, ejecutar, ejecutar_transaccion


def listar_tipos():
    return [dict(fila) for fila in consultar_todos("SELECT id, nombre FROM tipos_producto ORDER BY id")]


def crear_tipo(datos):
    nombre = datos.get("nombre", "").strip()
    if len(nombre) < 3:
        return False, "Ingresa un nombre de tipo valido."
    if consultar_uno("SELECT id FROM tipos_producto WHERE LOWER(nombre) = LOWER(%s)", (nombre,)):
        return False, "Ese tipo de producto ya existe."

    def operacion(cursor):
        cursor.execute("INSERT INTO tipos_producto (nombre) VALUES (%s)", (nombre,))
        cursor.execute(
            "INSERT INTO categorias (tipo_id, nombre) VALUES (%s, 'Sin clasificar')",
            (cursor.lastrowid,),
        )

    ejecutar_transaccion(operacion)
    return True, "Tipo de producto creado correctamente."


def editar_tipo(tipo_id, datos):
    nombre = datos.get("nombre", "").strip()
    if len(nombre) < 3:
        return False, "Ingresa un nombre de tipo valido."
    if not consultar_uno("SELECT id FROM tipos_producto WHERE id = %s", (tipo_id,)):
        return False, "El tipo solicitado no existe."
    if consultar_uno(
        "SELECT id FROM tipos_producto WHERE LOWER(nombre) = LOWER(%s) AND id <> %s",
        (nombre, tipo_id),
    ):
        return False, "Ese tipo de producto ya existe."
    ejecutar("UPDATE tipos_producto SET nombre = %s WHERE id = %s", (nombre, tipo_id))
    return True, "Tipo de producto actualizado correctamente."


def eliminar_tipo(tipo_id):
    tipo = consultar_uno(
        """
        SELECT t.id,
               (SELECT COUNT(*) FROM categorias c
                WHERE c.tipo_id = t.id AND LOWER(c.nombre) <> 'sin clasificar') AS categorias,
               (SELECT COUNT(*) FROM productos p WHERE p.tipo_id = t.id) AS productos
        FROM tipos_producto t
        WHERE t.id = %s
        """,
        (tipo_id,),
    )
    if not tipo:
        return False, "El tipo solicitado no existe."
    if tipo["categorias"] > 0 or tipo["productos"] > 0:
        return False, "No puedes eliminar un tipo que contiene categorias o productos."

    def operacion(cursor):
        cursor.execute("DELETE FROM categorias WHERE tipo_id = %s", (tipo_id,))
        cursor.execute("DELETE FROM tipos_producto WHERE id = %s", (tipo_id,))

    ejecutar_transaccion(operacion)
    return True, "Tipo de producto eliminado correctamente."


def preparar_categorias_generales():
    ejecutar(
        """
        INSERT INTO categorias (tipo_id, nombre)
        SELECT t.id, 'Sin clasificar'
        FROM tipos_producto t
        LEFT JOIN categorias c
          ON c.tipo_id = t.id AND LOWER(c.nombre) = 'sin clasificar'
        WHERE c.id IS NULL
        """
    )


def listar_unidades():
    filas = consultar_todos(
        "SELECT id, nombre, abreviatura, permite_decimal FROM unidades_medida ORDER BY id"
    )
    return [dict(fila) for fila in filas]


def listar_categorias():
    filas = consultar_todos(
        """
        SELECT c.id, c.nombre, c.tipo_id, t.nombre AS tipo
        FROM categorias c
        INNER JOIN tipos_producto t ON t.id = c.tipo_id
        ORDER BY t.id, c.nombre
        """
    )
    return [dict(fila) for fila in filas]


def listar_productos():
    productos = [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT p.id, p.nombre, p.marca, p.descripcion, p.stock_actual, p.stock_minimo,
                   p.observaciones, p.tipo_id, t.nombre AS tipo, p.categoria_id,
                   c.nombre AS categoria, p.unidad_base_id, u.nombre AS unidad,
                   u.abreviatura, u.permite_decimal
            FROM productos p
            INNER JOIN tipos_producto t ON t.id = p.tipo_id
            INNER JOIN categorias c ON c.id = p.categoria_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            ORDER BY p.nombre
            """
        )
    ]
    presentaciones = consultar_todos(
        "SELECT id, producto_id, nombre, factor FROM presentaciones_producto ORDER BY id"
    )
    por_producto = {}
    for presentacion in presentaciones:
        por_producto.setdefault(presentacion["producto_id"], []).append(dict(presentacion))
    for producto in productos:
        producto["presentaciones"] = por_producto.get(producto["id"], [])
    return productos


def resumen_productos(productos=None):
    productos = productos if productos is not None else listar_productos()
    return {
        "total": len(productos),
        "repuestos": sum(1 for producto in productos if producto["tipo"] == "Repuesto"),
        "lubricantes": sum(1 for producto in productos if producto["tipo"] == "Lubricante"),
        "bajo_stock": sum(
            1
            for producto in productos
            if producto["stock_minimo"] > 0 and producto["stock_actual"] <= producto["stock_minimo"]
        ),
    }


def listar_ajustes_stock(limite=20):
    filas = consultar_todos(
        """
        SELECT a.id, a.stock_anterior, a.stock_nuevo, a.diferencia, a.motivo, a.creado_en,
               p.nombre AS producto, u.abreviatura,
               COALESCE(us.nombre, 'Usuario eliminado') AS usuario
        FROM ajustes_stock a
        INNER JOIN productos p ON p.id = a.producto_id
        INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
        LEFT JOIN usuarios us ON us.id = a.usuario_id
        ORDER BY a.id DESC
        LIMIT %s
        """,
        (limite,),
    )
    return [dict(fila) for fila in filas]


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
    if numero < 0:
        return None, f"{nombre} no puede ser negativo."
    return numero.quantize(Decimal("0.001")), None


def _presentaciones_desde_formulario(datos):
    nombres = datos.getlist("presentacion_nombre") if hasattr(datos, "getlist") else []
    factores = datos.getlist("presentacion_factor") if hasattr(datos, "getlist") else []
    presentaciones = []
    usados = set()

    for nombre, factor_texto in zip(nombres, factores):
        nombre = nombre.strip()
        factor_texto = factor_texto.strip()
        if not nombre and not factor_texto:
            continue
        if not nombre or not factor_texto:
            return None, "Completa el nombre y la equivalencia de cada presentacion."
        factor, error = _decimal(factor_texto, "La equivalencia")
        if error or factor == 0:
            return None, error or "La equivalencia debe ser mayor que cero."
        clave = nombre.lower()
        if clave in usados:
            return None, "No repitas el nombre de una presentacion."
        usados.add(clave)
        presentaciones.append({"nombre": nombre, "factor": factor})

    return presentaciones, None


def _datos_producto(datos, incluir_stock=False):
    valores = {
        "nombre": datos.get("nombre", "").strip(),
        "tipo_id": _entero(datos.get("tipo_id")),
        "categoria_id": _entero(datos.get("categoria_id")),
        "marca": datos.get("marca", "").strip() or None,
        "descripcion": datos.get("descripcion", "").strip() or None,
        "unidad_base_id": _entero(datos.get("unidad_base_id")),
        "observaciones": datos.get("observaciones", "").strip() or None,
    }
    valores["stock_minimo"], error_minimo = _decimal(datos.get("stock_minimo"), "El stock minimo")
    if incluir_stock:
        valores["stock_actual"], error_stock = _decimal(datos.get("stock_actual"), "El stock inicial")
    else:
        error_stock = None
    valores["presentaciones"], error_presentaciones = _presentaciones_desde_formulario(datos)
    return valores, error_minimo or error_stock or error_presentaciones


def _validar_producto(valores, producto_id=None):
    if len(valores["nombre"]) < 3:
        return "Ingresa un nombre de producto valido."
    if not valores["tipo_id"] or not valores["categoria_id"] or not valores["unidad_base_id"]:
        return "Selecciona el tipo, la categoria y la unidad base."

    categoria = consultar_uno(
        "SELECT id FROM categorias WHERE id = %s AND tipo_id = %s",
        (valores["categoria_id"], valores["tipo_id"]),
    )
    if not categoria:
        return "La categoria no pertenece al tipo seleccionado."
    unidad = consultar_uno(
        "SELECT id, permite_decimal FROM unidades_medida WHERE id = %s",
        (valores["unidad_base_id"],),
    )
    if not unidad:
        return "La unidad seleccionada no existe."
    if not unidad["permite_decimal"]:
        cantidades = [valores["stock_minimo"]]
        if "stock_actual" in valores:
            cantidades.append(valores["stock_actual"])
        cantidades.extend(presentacion["factor"] for presentacion in valores["presentaciones"])
        if any(cantidad != cantidad.to_integral_value() for cantidad in cantidades):
            return "Las cantidades deben ser enteras para la unidad seleccionada."

    sql = """
        SELECT id FROM productos
        WHERE LOWER(nombre) = LOWER(%s)
          AND LOWER(COALESCE(marca, '')) = LOWER(%s)
    """
    parametros = [valores["nombre"], valores["marca"] or ""]
    if producto_id:
        sql += " AND id <> %s"
        parametros.append(producto_id)
    if consultar_uno(sql, tuple(parametros)):
        return "Ya existe un producto con el mismo nombre y marca."
    return None


def crear_producto(datos, usuario_id):
    valores, error = _datos_producto(datos, incluir_stock=True)
    if error:
        return False, error
    error = _validar_producto(valores)
    if error:
        return False, error

    def operacion(cursor):
        cursor.execute(
            """
            INSERT INTO productos
                (nombre, tipo_id, categoria_id, marca, descripcion, unidad_base_id,
                 stock_actual, stock_minimo, observaciones, creado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                valores["nombre"], valores["tipo_id"], valores["categoria_id"],
                valores["marca"], valores["descripcion"], valores["unidad_base_id"],
                valores["stock_actual"], valores["stock_minimo"], valores["observaciones"],
                usuario_id,
            ),
        )
        producto_id = cursor.lastrowid
        for presentacion in valores["presentaciones"]:
            cursor.execute(
                "INSERT INTO presentaciones_producto (producto_id, nombre, factor) VALUES (%s, %s, %s)",
                (producto_id, presentacion["nombre"], presentacion["factor"]),
            )
        if valores["stock_actual"] > 0:
            cursor.execute(
                """
                INSERT INTO ajustes_stock
                    (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
                VALUES (%s, 0, %s, %s, %s, %s)
                """,
                (
                    producto_id,
                    valores["stock_actual"],
                    valores["stock_actual"],
                    "Inventario inicial",
                    usuario_id,
                ),
            )
        return producto_id

    ejecutar_transaccion(operacion)
    return True, "Producto registrado correctamente."


def editar_producto(producto_id, datos):
    actual = consultar_uno(
        "SELECT id, unidad_base_id, stock_actual FROM productos WHERE id = %s",
        (producto_id,),
    )
    if not actual:
        return False, "El producto solicitado no existe."
    valores, error = _datos_producto(datos)
    if error:
        return False, error
    if actual["stock_actual"] != 0 and valores["unidad_base_id"] != actual["unidad_base_id"]:
        return False, "No puedes cambiar la unidad base de un producto que ya tiene stock."
    error = _validar_producto(valores, producto_id=producto_id)
    if error:
        return False, error

    def operacion(cursor):
        cursor.execute(
            """
            UPDATE productos
            SET nombre = %s, tipo_id = %s, categoria_id = %s, marca = %s,
                descripcion = %s, unidad_base_id = %s, stock_minimo = %s,
                observaciones = %s
            WHERE id = %s
            """,
            (
                valores["nombre"], valores["tipo_id"], valores["categoria_id"],
                valores["marca"], valores["descripcion"], valores["unidad_base_id"],
                valores["stock_minimo"], valores["observaciones"], producto_id,
            ),
        )
        cursor.execute("DELETE FROM presentaciones_producto WHERE producto_id = %s", (producto_id,))
        for presentacion in valores["presentaciones"]:
            cursor.execute(
                "INSERT INTO presentaciones_producto (producto_id, nombre, factor) VALUES (%s, %s, %s)",
                (producto_id, presentacion["nombre"], presentacion["factor"]),
            )

    ejecutar_transaccion(operacion)
    return True, "Producto actualizado correctamente."


def ajustar_stock_producto(producto_id, datos, usuario_id):
    stock_nuevo, error = _decimal(datos.get("stock_nuevo"), "El nuevo stock")
    motivo = datos.get("motivo", "").strip()
    if error:
        return False, error
    if len(motivo) < 3:
        return False, "Ingresa el motivo del ajuste."

    def operacion(cursor):
        cursor.execute(
            """
            SELECT p.id, p.stock_actual, u.permite_decimal
            FROM productos p
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            WHERE p.id = %s
            FOR UPDATE
            """,
            (producto_id,),
        )
        producto = cursor.fetchone()
        if not producto:
            return False, "El producto solicitado no existe."
        if not producto["permite_decimal"] and stock_nuevo != stock_nuevo.to_integral_value():
            return False, "El stock debe ser entero para la unidad seleccionada."

        diferencia = stock_nuevo - producto["stock_actual"]
        if diferencia == 0:
            return False, "El nuevo stock es igual al stock actual."
        cursor.execute("UPDATE productos SET stock_actual = %s WHERE id = %s", (stock_nuevo, producto_id))
        cursor.execute(
            """
            INSERT INTO ajustes_stock
                (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                producto_id,
                producto["stock_actual"],
                stock_nuevo,
                diferencia,
                motivo,
                usuario_id,
            ),
        )
        return True, "Stock ajustado correctamente."

    return ejecutar_transaccion(operacion)


def eliminar_producto(producto_id):
    producto = consultar_uno(
        """
        SELECT p.id, p.stock_actual,
               (SELECT COUNT(*) FROM ajustes_stock a WHERE a.producto_id = p.id) AS ajustes
        FROM productos p
        WHERE p.id = %s
        """,
        (producto_id,),
    )
    if not producto:
        return False, "El producto solicitado no existe."
    if producto["stock_actual"] != 0 or producto["ajustes"] > 0:
        return False, "No puedes eliminar un producto que ya tiene historial de stock."
    ejecutar("DELETE FROM productos WHERE id = %s", (producto_id,))
    return True, "Producto eliminado correctamente."


def crear_categoria(datos):
    tipo_id = _entero(datos.get("tipo_id"))
    nombre = datos.get("nombre", "").strip()
    if not tipo_id or len(nombre) < 3:
        return False, "Selecciona un tipo e ingresa una categoria valida."
    if not consultar_uno("SELECT id FROM tipos_producto WHERE id = %s", (tipo_id,)):
        return False, "El tipo de producto no existe."
    if consultar_uno(
        "SELECT id FROM categorias WHERE tipo_id = %s AND LOWER(nombre) = LOWER(%s)",
        (tipo_id, nombre),
    ):
        return False, "Esa categoria ya existe para el tipo seleccionado."
    ejecutar("INSERT INTO categorias (tipo_id, nombre) VALUES (%s, %s)", (tipo_id, nombre))
    return True, "Categoria creada correctamente."


def eliminar_categoria(categoria_id):
    categoria = consultar_uno(
        """
        SELECT c.id, c.nombre,
               (SELECT COUNT(*) FROM productos p WHERE p.categoria_id = c.id) AS productos
        FROM categorias c
        WHERE c.id = %s
        """,
        (categoria_id,),
    )
    if not categoria:
        return False, "La categoria solicitada no existe."
    if categoria["nombre"].strip().lower() == "sin clasificar":
        return False, "La categoria Sin clasificar es necesaria para registrar productos generales."
    if categoria["productos"] > 0:
        return False, "No puedes eliminar una categoria que contiene productos."
    ejecutar("DELETE FROM categorias WHERE id = %s", (categoria_id,))
    return True, "Categoria eliminada correctamente."
