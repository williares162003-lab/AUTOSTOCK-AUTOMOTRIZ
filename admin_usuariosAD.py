from bd import consultar_todos


def listar_usuarios():
    filas = consultar_todos(
        """
        SELECT id, usuario, nombre, correo, documento, rol, estado, ultimo_acceso
        FROM usuarios
        ORDER BY id ASC
        """
    )
    return [dict(fila) for fila in filas]


def resumen_usuarios():
    usuarios = listar_usuarios()
    return {
        "total": len(usuarios),
        "activos": sum(1 for usuario in usuarios if usuario["estado"] == "activo"),
        "inactivos": sum(1 for usuario in usuarios if usuario["estado"] == "inactivo"),
        "suspendidos": sum(1 for usuario in usuarios if usuario["estado"] == "suspendido"),
    }
