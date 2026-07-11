import re

from werkzeug.security import generate_password_hash

from bd import consultar_todos, consultar_uno, ejecutar


ROLES_VALIDOS = {"ADMIN", "ALMACEN"}
ESTADOS_VALIDOS = {"activo", "inactivo", "suspendido"}
USUARIO_PATRON = re.compile(r"^[A-Za-z0-9._-]{3,40}$")


def listar_usuarios():
    filas = consultar_todos(
        """
        SELECT id, usuario, nombre, correo, documento, rol, estado, ultimo_acceso
        FROM usuarios
        ORDER BY id ASC
        """
    )
    return [dict(fila) for fila in filas]


def obtener_usuario(usuario_id):
    fila = consultar_uno(
        """
        SELECT id, usuario, nombre, correo, documento, rol, estado, ultimo_acceso
        FROM usuarios
        WHERE id = %s
        """,
        (usuario_id,),
    )
    return dict(fila) if fila else None


def resumen_usuarios():
    usuarios = listar_usuarios()
    return {
        "total": len(usuarios),
        "activos": sum(1 for usuario in usuarios if usuario["estado"] == "activo"),
        "inactivos": sum(1 for usuario in usuarios if usuario["estado"] == "inactivo"),
        "suspendidos": sum(1 for usuario in usuarios if usuario["estado"] == "suspendido"),
    }


def _datos_usuario(datos, incluir_password=False):
    valores = {
        "usuario": datos.get("usuario", "").strip(),
        "nombre": datos.get("nombre", "").strip(),
        "correo": datos.get("correo", "").strip().lower(),
        "documento": datos.get("documento", "").strip(),
        "rol": datos.get("rol", "").strip().upper(),
        "estado": datos.get("estado", "activo").strip().lower(),
    }
    if incluir_password:
        valores["contrasena"] = datos.get("contrasena", "")
        valores["confirmar_contrasena"] = datos.get("confirmar_contrasena", "")
    return valores


def _validar_datos(valores, incluir_password=False):
    if not USUARIO_PATRON.fullmatch(valores["usuario"]):
        return "El usuario debe tener entre 3 y 40 caracteres validos."
    if len(valores["nombre"]) < 3:
        return "Ingresa el nombre completo del usuario."
    if "@" not in valores["correo"] or "." not in valores["correo"].split("@")[-1]:
        return "Ingresa un correo valido."
    if not valores["documento"]:
        return "Ingresa el DNI o documento."
    if valores["rol"] not in ROLES_VALIDOS:
        return "El rol seleccionado no es valido."
    if valores["estado"] not in ESTADOS_VALIDOS:
        return "El estado seleccionado no es valido."
    if incluir_password and len(valores["contrasena"]) < 8:
        return "La contrasena debe tener al menos 8 caracteres."
    if incluir_password and valores["contrasena"] != valores["confirmar_contrasena"]:
        return "Las contrasenas no coinciden."
    return None


def crear_usuario(datos):
    valores = _datos_usuario(datos, incluir_password=True)
    error = _validar_datos(valores, incluir_password=True)
    if error:
        return False, error

    existente = consultar_uno("SELECT id FROM usuarios WHERE usuario = %s", (valores["usuario"],))
    if existente:
        return False, "Ese nombre de usuario ya existe."

    ejecutar(
        """
        INSERT INTO usuarios (usuario, password_hash, nombre, correo, documento, rol, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            valores["usuario"],
            generate_password_hash(valores["contrasena"]),
            valores["nombre"],
            valores["correo"],
            valores["documento"],
            valores["rol"],
            valores["estado"],
        ),
    )
    return True, "Usuario creado correctamente."


def editar_usuario(usuario_id, datos, administrador_id):
    actual = obtener_usuario(usuario_id)
    if not actual:
        return False, "El usuario solicitado no existe."

    valores = _datos_usuario(datos)
    error = _validar_datos(valores)
    if error:
        return False, error
    if usuario_id == administrador_id and valores["rol"] != "ADMIN":
        return False, "No puedes retirar tu propio rol de administrador."
    if usuario_id == administrador_id and valores["estado"] != "activo":
        return False, "No puedes desactivar tu propia cuenta."

    repetido = consultar_uno(
        "SELECT id FROM usuarios WHERE usuario = %s AND id <> %s",
        (valores["usuario"], usuario_id),
    )
    if repetido:
        return False, "Ese nombre de usuario ya existe."

    ejecutar(
        """
        UPDATE usuarios
        SET usuario = %s, nombre = %s, correo = %s, documento = %s, rol = %s, estado = %s
        WHERE id = %s
        """,
        (
            valores["usuario"],
            valores["nombre"],
            valores["correo"],
            valores["documento"],
            valores["rol"],
            valores["estado"],
            usuario_id,
        ),
    )
    return True, "Usuario actualizado correctamente."


def cambiar_estado_usuario(usuario_id, estado, administrador_id):
    estado = estado.strip().lower()
    if estado not in ESTADOS_VALIDOS:
        return False, "El estado seleccionado no es valido."
    if usuario_id == administrador_id and estado != "activo":
        return False, "No puedes desactivar tu propia cuenta."
    if not obtener_usuario(usuario_id):
        return False, "El usuario solicitado no existe."

    ejecutar("UPDATE usuarios SET estado = %s WHERE id = %s", (estado, usuario_id))
    return True, "Estado del usuario actualizado."


def cambiar_password_usuario(usuario_id, contrasena, confirmar_contrasena):
    if len(contrasena) < 8:
        return False, "La contrasena debe tener al menos 8 caracteres."
    if contrasena != confirmar_contrasena:
        return False, "Las contrasenas no coinciden."
    if not obtener_usuario(usuario_id):
        return False, "El usuario solicitado no existe."

    ejecutar(
        "UPDATE usuarios SET password_hash = %s WHERE id = %s",
        (generate_password_hash(contrasena), usuario_id),
    )
    return True, "Contrasena actualizada correctamente."
