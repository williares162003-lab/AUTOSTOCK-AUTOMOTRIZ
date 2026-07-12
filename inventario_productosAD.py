from decimal import Decimal, InvalidOperation

from bd import consultar_todos, consultar_uno, ejecutar, ejecutar_transaccion


def listar_tipos():
    return [dict(fila) for fila in consultar_todos("SELECT id, nombre FROM tipos_producto ORDER BY id")]


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


def editar_categoria(categoria_id, datos):
    tipo_id = _entero(datos.get("tipo_id"))
    nombre = datos.get("nombre", "").strip()
    if not tipo_id or len(nombre) < 3:
        return False, "Selecciona un tipo e ingresa una categoria valida."
    if not consultar_uno("SELECT id FROM categorias WHERE id = %s", (categoria_id,)):
        return False, "La categoria solicitada no existe."
    if consultar_uno(
        "SELECT id FROM categorias WHERE tipo_id = %s AND LOWER(nombre) = LOWER(%s) AND id <> %s",
        (tipo_id, nombre, categoria_id),
    ):
        return False, "Esa categoria ya existe para el tipo seleccionado."
    ejecutar("UPDATE categorias SET tipo_id = %s, nombre = %s WHERE id = %s", (tipo_id, nombre, categoria_id))
    return True, "Categoria actualizada correctamente."
