from decimal import Decimal, InvalidOperation

from bd import consultar_todos, consultar_uno, ejecutar, ejecutar_transaccion


def listar_areas():
    filas = consultar_todos("SELECT id, nombre FROM areas_almacen ORDER BY id")
    return [dict(fila) for fila in filas]


def listar_tipos():
    return [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT t.id, t.nombre, t.area_id, a.nombre AS area
            FROM tipos_producto t
            INNER JOIN areas_almacen a ON a.id = t.area_id
            ORDER BY a.id, t.nombre
            """
        )
    ]


def crear_tipo(datos):
    nombre = datos.get("nombre", "").strip()
    area_id = _entero(datos.get("area_id")) or _area_mecanica_id()
    if len(nombre) < 3:
        return False, "Ingresa un nombre de tipo valido."
    if not consultar_uno("SELECT id FROM areas_almacen WHERE id = %s", (area_id,)):
        return False, "Selecciona un area valida."
    if consultar_uno(
        "SELECT id FROM tipos_producto WHERE area_id = %s AND LOWER(nombre) = LOWER(%s)",
        (area_id, nombre),
    ):
        return False, "Ese tipo de producto ya existe en esa area."

    def operacion(cursor):
        cursor.execute("INSERT INTO tipos_producto (area_id, nombre) VALUES (%s, %s)", (area_id, nombre))
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
    actual = consultar_uno("SELECT id, area_id FROM tipos_producto WHERE id = %s", (tipo_id,))
    if not actual:
        return False, "El tipo solicitado no existe."
    area_id = _entero(datos.get("area_id")) or actual["area_id"]
    if not consultar_uno("SELECT id FROM areas_almacen WHERE id = %s", (area_id,)):
        return False, "Selecciona un area valida."
    if consultar_uno(
        "SELECT id FROM tipos_producto WHERE area_id = %s AND LOWER(nombre) = LOWER(%s) AND id <> %s",
        (area_id, nombre, tipo_id),
    ):
        return False, "Ese tipo de producto ya existe en esa area."
    ejecutar("UPDATE tipos_producto SET area_id = %s, nombre = %s WHERE id = %s", (area_id, nombre, tipo_id))
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


def _area_mecanica_id():
    area = consultar_uno("SELECT id FROM areas_almacen WHERE LOWER(nombre) = 'mecanica' LIMIT 1")
    if area:
        return area["id"]
    return ejecutar("INSERT INTO areas_almacen (nombre) VALUES ('Mecanica')")


def listar_unidades():
    filas = consultar_todos(
        "SELECT id, nombre, abreviatura, permite_decimal FROM unidades_medida ORDER BY id"
    )
    return [dict(fila) for fila in filas]


def listar_categorias():
    filas = consultar_todos(
        """
        SELECT c.id, c.nombre, c.tipo_id, t.nombre AS tipo,
               t.area_id, a.nombre AS area
        FROM categorias c
        INNER JOIN tipos_producto t ON t.id = c.tipo_id
        INNER JOIN areas_almacen a ON a.id = t.area_id
        ORDER BY a.id, t.nombre, c.nombre
        """
    )
    return [dict(fila) for fila in filas]


def _es_galon(abreviatura):
    return "gal" in (abreviatura or "").lower()


def _unidad_operativa(abreviatura):
    return "L" if _es_galon(abreviatura) else abreviatura


def _a_decimal(valor):
    return Decimal(str(valor or "0"))


def _dividir_stock(valor, divisor):
    divisor = _a_decimal(divisor)
    if divisor <= 0:
        return Decimal("0.000")
    return (_a_decimal(valor) / divisor).quantize(Decimal("0.001"))


def listar_productos():
    productos = [
        dict(fila)
        for fila in consultar_todos(
            """
            SELECT p.id, p.nombre, p.codigo, p.marca, p.descripcion, p.stock_actual,
                   p.stock_suelto, p.stock_balde_abierto, p.baldes_abiertos,
                   p.stock_baldes_cerrados, p.stock_cilindro_abierto,
                   p.cilindros_abiertos, p.stock_cilindros_cerrados,
                   p.litros_por_cilindro, p.litros_por_galon, p.stock_cajas_cerradas,
                   p.unidades_por_caja,
                   p.stock_minimo,
                   p.observaciones, p.tipo_id, t.nombre AS tipo, t.area_id,
                   a.nombre AS area, p.categoria_id,
                   c.nombre AS categoria, p.unidad_base_id, u.nombre AS unidad,
                   u.abreviatura, u.permite_decimal
            FROM productos p
            INNER JOIN tipos_producto t ON t.id = p.tipo_id
            INNER JOIN areas_almacen a ON a.id = t.area_id
            INNER JOIN categorias c ON c.id = p.categoria_id
            INNER JOIN unidades_medida u ON u.id = p.unidad_base_id
            ORDER BY a.id, t.nombre, c.nombre, p.nombre
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
        producto["es_galon"] = _es_galon(producto["abreviatura"])
        producto["unidad_operativa"] = _unidad_operativa(producto["abreviatura"])
        producto["presentaciones"] = por_producto.get(producto["id"], [])
        producto["stock_en_cajas"] = (
            producto.get("stock_cajas_cerradas", 0) * producto.get("unidades_por_caja", 0)
        )
        capacidad_cilindro = producto.get("litros_por_cilindro", 0)
        cilindros_abiertos = producto.get("cilindros_abiertos", 0)
        cilindros_cerrados = producto.get("stock_cilindros_cerrados", 0)
        usado_cilindro = producto.get("stock_cilindro_abierto", 0)
        producto["stock_cilindro_disponible"] = max(
            (cilindros_abiertos * capacidad_cilindro) - usado_cilindro,
            0,
        )
        producto["stock_cilindros_cerrados_litros"] = cilindros_cerrados * capacidad_cilindro
        producto["stock_total"] = (
            producto["stock_actual"]
            + producto["stock_en_cajas"]
            + producto["stock_cilindro_disponible"]
            + producto["stock_cilindros_cerrados_litros"]
        )
        litros_por_galon = producto.get("litros_por_galon", 0)
        producto["stock_actual_envases"] = _dividir_stock(producto["stock_actual"], litros_por_galon)
        producto["stock_suelto_envases"] = _dividir_stock(producto["stock_suelto"], litros_por_galon)
        producto["stock_total_envases"] = _dividir_stock(producto["stock_total"], litros_por_galon)
    return productos


def resumen_productos(productos=None):
    productos = productos if productos is not None else listar_productos()
    con_stock = sum(
        1
        for producto in productos
        if producto["stock_actual"] > 0
        or producto.get("stock_baldes_cerrados", 0) > 0
        or producto.get("baldes_abiertos", 0) > 0
        or producto.get("stock_cilindros_cerrados", 0) > 0
        or producto.get("cilindros_abiertos", 0) > 0
        or producto.get("stock_cajas_cerradas", 0) > 0
    )
    return {
        "total": len(productos),
        "con_stock": con_stock,
        "sin_stock": sum(
            1
            for producto in productos
            if producto["stock_actual"] <= 0
            and producto.get("stock_baldes_cerrados", 0) <= 0
            and producto.get("baldes_abiertos", 0) <= 0
            and producto.get("stock_cilindros_cerrados", 0) <= 0
            and producto.get("cilindros_abiertos", 0) <= 0
            and producto.get("stock_cajas_cerradas", 0) <= 0
        ),
        "repuestos": sum(1 for producto in productos if producto["tipo"] == "Repuesto"),
        "lubricantes": sum(1 for producto in productos if producto["tipo"] == "Lubricante"),
        "bajo_stock": sum(
            1
            for producto in productos
            if producto.get("stock_total", producto["stock_actual"]) > 0
            and producto["stock_minimo"] > 0
            and producto.get("stock_total", producto["stock_actual"]) <= producto["stock_minimo"]
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
    ajustes = []
    for fila in filas:
        ajuste = dict(fila)
        ajuste["abreviatura"] = _unidad_operativa(ajuste["abreviatura"])
        ajustes.append(ajuste)
    return ajustes


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


def _normalizar_texto(valor):
    return (valor or "").strip().casefold()


def _firma_presentaciones(presentaciones):
    return tuple(
        sorted(
            (
                _normalizar_texto(presentacion["nombre"]),
                Decimal(str(presentacion["factor"])).quantize(Decimal("0.001")),
            )
            for presentacion in presentaciones
        )
    )


def _firmas_presentaciones_por_producto(producto_ids):
    if not producto_ids:
        return {}
    marcadores = ", ".join(["%s"] * len(producto_ids))
    filas = consultar_todos(
        f"""
        SELECT producto_id, nombre, factor
        FROM presentaciones_producto
        WHERE producto_id IN ({marcadores})
        ORDER BY producto_id, nombre
        """,
        tuple(producto_ids),
    )
    por_producto = {producto_id: [] for producto_id in producto_ids}
    for fila in filas:
        por_producto.setdefault(fila["producto_id"], []).append(
            {"nombre": fila["nombre"], "factor": fila["factor"]}
        )
    return {
        producto_id: _firma_presentaciones(presentaciones)
        for producto_id, presentaciones in por_producto.items()
    }


def _datos_producto(datos, incluir_stock=False):
    valores = {
        "nombre": datos.get("nombre", "").strip(),
        "codigo": datos.get("codigo", "").strip().upper() or None,
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
        valores["litros_por_galon"], error_litros_galon = _decimal(
            datos.get("litros_por_galon"),
            "Los litros por galon",
        )
    else:
        error_stock = None
        error_litros_galon = None
    valores["presentaciones"], error_presentaciones = _presentaciones_desde_formulario(datos)
    return valores, error_minimo or error_stock or error_litros_galon or error_presentaciones


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
        "SELECT id, permite_decimal, abreviatura FROM unidades_medida WHERE id = %s",
        (valores["unidad_base_id"],),
    )
    if not unidad:
        return "La unidad seleccionada no existe."
    valores["es_galon"] = _es_galon(unidad.get("abreviatura", ""))
    if valores["es_galon"] and "stock_actual" in valores:
        if valores["stock_actual"] > 0 and valores["litros_por_galon"] <= 0:
            return "Indica cuantos litros trae cada galon/envase."
        if valores["stock_actual"] != valores["stock_actual"].to_integral_value():
            return "La cantidad inicial de galones/envases debe ser entera."
    if not unidad["permite_decimal"]:
        cantidades = [valores["stock_minimo"]]
        if "stock_actual" in valores:
            cantidades.append(valores["stock_actual"])
        cantidades.extend(presentacion["factor"] for presentacion in valores["presentaciones"])
        if any(cantidad != cantidad.to_integral_value() for cantidad in cantidades):
            return "Las cantidades deben ser enteras para la unidad seleccionada."

    if valores.get("codigo"):
        sql_codigo = """
            SELECT id, nombre, marca
            FROM productos
            WHERE LOWER(codigo) = LOWER(%s)
        """
        parametros_codigo = [valores["codigo"]]
        if producto_id:
            sql_codigo += " AND id <> %s"
            parametros_codigo.append(producto_id)
        candidatos = consultar_todos(sql_codigo, tuple(parametros_codigo))
        firmas_existentes = _firmas_presentaciones_por_producto([fila["id"] for fila in candidatos])
        firma_actual = _firma_presentaciones(valores["presentaciones"])
        for candidato in candidatos:
            mismo_producto = (
                _normalizar_texto(candidato["nombre"]) == _normalizar_texto(valores["nombre"])
                and _normalizar_texto(candidato["marca"]) == _normalizar_texto(valores["marca"])
            )
            if mismo_producto and firmas_existentes.get(candidato["id"], tuple()) == firma_actual:
                return "Ya existe un producto con ese codigo, nombre y presentacion."
    else:
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
    stock_inicial = valores["stock_actual"]
    litros_por_galon = Decimal("0.000")
    if valores.get("es_galon"):
        litros_por_galon = valores["litros_por_galon"]
        stock_inicial = (valores["stock_actual"] * litros_por_galon).quantize(Decimal("0.001"))

    def operacion(cursor):
        cursor.execute(
            """
            INSERT INTO productos
                (nombre, codigo, tipo_id, categoria_id, marca, descripcion, unidad_base_id,
                 stock_actual, stock_suelto, litros_por_galon, stock_minimo, observaciones, creado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                valores["nombre"], valores["codigo"], valores["tipo_id"], valores["categoria_id"],
                valores["marca"], valores["descripcion"], valores["unidad_base_id"],
                stock_inicial, stock_inicial, litros_por_galon,
                valores["stock_minimo"], valores["observaciones"],
                usuario_id,
            ),
        )
        producto_id = cursor.lastrowid
        for presentacion in valores["presentaciones"]:
            cursor.execute(
                "INSERT INTO presentaciones_producto (producto_id, nombre, factor) VALUES (%s, %s, %s)",
                (producto_id, presentacion["nombre"], presentacion["factor"]),
            )
        if stock_inicial > 0:
            cursor.execute(
                """
                INSERT INTO ajustes_stock
                    (producto_id, stock_anterior, stock_nuevo, diferencia, motivo, usuario_id)
                VALUES (%s, 0, %s, %s, %s, %s)
                """,
                (
                    producto_id,
                    stock_inicial,
                    stock_inicial,
                    (
                        f"Inventario inicial: {valores['stock_actual']} galon(es) "
                        f"de {litros_por_galon} L"
                        if valores.get("es_galon")
                        else "Inventario inicial"
                    ),
                    usuario_id,
                ),
            )
        return producto_id

    ejecutar_transaccion(operacion)
    return True, "Producto registrado correctamente."


def editar_producto(producto_id, datos):
    actual = consultar_uno(
        """
        SELECT id, unidad_base_id, stock_actual, stock_suelto,
               stock_balde_abierto, baldes_abiertos, stock_baldes_cerrados,
               stock_cilindro_abierto, cilindros_abiertos, stock_cilindros_cerrados,
               litros_por_galon, stock_cajas_cerradas, unidades_por_caja
        FROM productos
        WHERE id = %s
        """,
        (producto_id,),
    )
    if not actual:
        return False, "El producto solicitado no existe."
    valores, error = _datos_producto(datos)
    if error:
        return False, error
    stock_total = (
        actual["stock_suelto"]
        + actual["stock_balde_abierto"]
        + actual["baldes_abiertos"]
        + actual["stock_baldes_cerrados"]
        + actual["stock_cilindro_abierto"]
        + actual["cilindros_abiertos"]
        + actual["stock_cilindros_cerrados"]
        + actual["stock_cajas_cerradas"]
    )
    if stock_total != 0 and valores["unidad_base_id"] != actual["unidad_base_id"]:
        return False, "No puedes cambiar la unidad base de un producto que ya tiene stock."
    error = _validar_producto(valores, producto_id=producto_id)
    if error:
        return False, error

    def operacion(cursor):
        cursor.execute(
            """
            UPDATE productos
            SET nombre = %s, codigo = %s, tipo_id = %s, categoria_id = %s, marca = %s,
                descripcion = %s, unidad_base_id = %s, stock_minimo = %s,
                observaciones = %s
            WHERE id = %s
            """,
            (
                valores["nombre"], valores["codigo"], valores["tipo_id"], valores["categoria_id"],
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
    stock_suelto, error_suelto = _decimal(
        datos.get("stock_suelto_nuevo", datos.get("stock_nuevo")),
        "El stock suelto",
    )
    stock_balde_abierto, error_balde_abierto = _decimal(
        datos.get("stock_balde_abierto_nuevo", "0"),
        "El consumo del balde abierto",
    )
    baldes_abiertos, error_baldes_abiertos = _decimal(
        datos.get("baldes_abiertos_nuevo", "0"),
        "Los baldes abiertos",
    )
    stock_baldes_cerrados, error_baldes_cerrados = _decimal(
        datos.get("stock_baldes_cerrados_nuevo", "0"),
        "Los baldes cerrados",
    )
    stock_cilindro_abierto, error_cilindro_abierto = _decimal(
        datos.get("stock_cilindro_abierto_nuevo", "0"),
        "El consumo del cilindro abierto",
    )
    cilindros_abiertos, error_cilindros_abiertos = _decimal(
        datos.get("cilindros_abiertos_nuevo", "0"),
        "Los cilindros abiertos",
    )
    stock_cilindros_cerrados, error_cilindros_cerrados = _decimal(
        datos.get("stock_cilindros_cerrados_nuevo", "0"),
        "Los cilindros cerrados",
    )
    litros_por_cilindro, error_litros_cilindro = _decimal(
        datos.get("litros_por_cilindro_nuevo", "0"),
        "Los litros por cilindro",
    )
    litros_por_galon, error_litros_galon = _decimal(
        datos.get("litros_por_galon_nuevo", "0"),
        "Los litros por galon",
    )
    stock_cajas_cerradas, error_cajas_cerradas = _decimal(
        datos.get("stock_cajas_cerradas_nuevo", "0"),
        "Las cajas cerradas",
    )
    unidades_por_caja, error_unidades_caja = _decimal(
        datos.get("unidades_por_caja_nuevo", "0"),
        "Las unidades por caja",
    )
    motivo = datos.get("motivo", "").strip()
    error = (
        error_suelto
        or error_balde_abierto
        or error_baldes_abiertos
        or error_baldes_cerrados
        or error_cilindro_abierto
        or error_cilindros_abiertos
        or error_cilindros_cerrados
        or error_litros_cilindro
        or error_litros_galon
        or error_cajas_cerradas
        or error_unidades_caja
    )
    if error:
        return False, error
    if len(motivo) < 3:
        return False, "Ingresa el motivo del ajuste."
    if (
        baldes_abiertos != baldes_abiertos.to_integral_value()
        or stock_baldes_cerrados != stock_baldes_cerrados.to_integral_value()
        or cilindros_abiertos != cilindros_abiertos.to_integral_value()
        or stock_cilindros_cerrados != stock_cilindros_cerrados.to_integral_value()
        or stock_cajas_cerradas != stock_cajas_cerradas.to_integral_value()
    ):
        return False, "Los baldes, cilindros y cajas cerradas deben ser enteros."

    def operacion(cursor):
        cursor.execute(
            """
            SELECT p.id, p.stock_actual, p.stock_suelto, p.stock_balde_abierto,
                   p.baldes_abiertos, p.stock_baldes_cerrados,
                   p.stock_cilindro_abierto, p.cilindros_abiertos,
                   p.stock_cilindros_cerrados, p.litros_por_cilindro, p.litros_por_galon,
                   p.stock_cajas_cerradas, p.unidades_por_caja,
                   u.permite_decimal
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
        if not producto["permite_decimal"]:
            cantidades = [stock_suelto, stock_balde_abierto, stock_cilindro_abierto, unidades_por_caja]
            if any(cantidad != cantidad.to_integral_value() for cantidad in cantidades):
                return False, "El stock debe ser entero para la unidad seleccionada."
        if (cilindros_abiertos > 0 or stock_cilindro_abierto > 0) and litros_por_cilindro <= 0:
            return False, "Indica los litros por cilindro si hay cilindros en uso."
        if stock_cilindro_abierto > litros_por_cilindro and litros_por_cilindro > 0:
            return False, "El consumo del cilindro abierto no puede superar los litros por cilindro."
        if stock_cajas_cerradas > 0 and unidades_por_caja <= 0:
            return False, "Indica cuantas unidades trae cada caja si hay cajas cerradas."

        sin_cambios = (
            stock_suelto == producto["stock_suelto"]
            and stock_balde_abierto == producto["stock_balde_abierto"]
            and baldes_abiertos == producto["baldes_abiertos"]
            and stock_baldes_cerrados == producto["stock_baldes_cerrados"]
            and stock_cilindro_abierto == producto["stock_cilindro_abierto"]
            and cilindros_abiertos == producto["cilindros_abiertos"]
            and stock_cilindros_cerrados == producto["stock_cilindros_cerrados"]
            and litros_por_cilindro == producto["litros_por_cilindro"]
            and litros_por_galon == producto["litros_por_galon"]
            and stock_cajas_cerradas == producto["stock_cajas_cerradas"]
            and unidades_por_caja == producto["unidades_por_caja"]
        )
        if sin_cambios:
            return False, "El nuevo stock es igual al stock actual."

        stock_nuevo = stock_suelto
        diferencia = stock_nuevo - producto["stock_actual"]
        cursor.execute(
            """
            UPDATE productos
            SET stock_suelto = %s,
                stock_balde_abierto = %s,
                baldes_abiertos = %s,
                stock_baldes_cerrados = %s,
                stock_cilindro_abierto = %s,
                cilindros_abiertos = %s,
                stock_cilindros_cerrados = %s,
                litros_por_cilindro = %s,
                litros_por_galon = %s,
                stock_cajas_cerradas = %s,
                unidades_por_caja = %s,
                stock_actual = %s
            WHERE id = %s
            """,
            (
                stock_suelto,
                stock_balde_abierto,
                baldes_abiertos,
                stock_baldes_cerrados,
                stock_cilindro_abierto,
                cilindros_abiertos,
                stock_cilindros_cerrados,
                litros_por_cilindro,
                litros_por_galon,
                stock_cajas_cerradas,
                unidades_por_caja,
                stock_nuevo,
                producto_id,
            ),
        )
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
        SELECT p.id, p.stock_actual, p.stock_suelto,
               p.stock_balde_abierto, p.baldes_abiertos, p.stock_baldes_cerrados,
               p.stock_cilindro_abierto, p.cilindros_abiertos, p.stock_cilindros_cerrados,
               p.litros_por_galon, p.stock_cajas_cerradas, p.unidades_por_caja
        FROM productos p
        WHERE p.id = %s
        """,
        (producto_id,),
    )
    if not producto:
        return False, "El producto solicitado no existe."
    stock_total = (
        producto["stock_suelto"]
        + producto["stock_balde_abierto"]
        + producto["baldes_abiertos"]
        + producto["stock_baldes_cerrados"]
        + producto["stock_cilindro_abierto"]
        + producto["cilindros_abiertos"]
        + producto["stock_cilindros_cerrados"]
        + producto["stock_cajas_cerradas"]
    )
    if stock_total != 0:
        return False, "Primero ajusta el stock del producto a cero para poder eliminarlo."

    def operacion(cursor):
        cursor.execute("DELETE FROM aperturas_balde WHERE producto_id = %s", (producto_id,))
        cursor.execute("DELETE FROM salidas_stock_detalle WHERE producto_id = %s", (producto_id,))
        cursor.execute(
            """
            DELETE s FROM salidas_stock s
            LEFT JOIN salidas_stock_detalle d ON d.salida_id = s.id
            WHERE d.id IS NULL
            """
        )
        cursor.execute("DELETE FROM entradas_stock WHERE producto_id = %s", (producto_id,))
        cursor.execute("DELETE FROM ajustes_stock WHERE producto_id = %s", (producto_id,))
        cursor.execute("DELETE FROM presentaciones_producto WHERE producto_id = %s", (producto_id,))
        cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))

    ejecutar_transaccion(operacion)
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
