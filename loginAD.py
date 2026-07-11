import os
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from bd import consultar_uno, ejecutar


def _usuario_desde_fila(fila):
    if not fila:
        return None
    return {
        "id": fila["id"],
        "usuario": fila["usuario"],
        "nombre": fila["nombre"],
        "correo": fila["correo"],
        "documento": fila["documento"],
        "rol": fila["rol"],
        "estado": fila["estado"],
        "ultimo_acceso": fila["ultimo_acceso"],
    }


def obtener_usuario_por_id(usuario_id):
    fila = consultar_uno(
        """
        SELECT id, usuario, nombre, correo, documento, rol, estado, ultimo_acceso
        FROM usuarios
        WHERE id = %s
        """,
        (usuario_id,),
    )
    return _usuario_desde_fila(fila)


def obtener_usuario_por_nombre(usuario):
    fila = consultar_uno(
        """
        SELECT id, usuario, nombre, correo, documento, rol, estado, ultimo_acceso, password_hash
        FROM usuarios
        WHERE usuario = %s
        """,
        (usuario,),
    )
    return fila


def autenticar_usuario(usuario, contrasena):
    fila = obtener_usuario_por_nombre(usuario.strip())
    if not fila:
        return None, "Usuario o contrasena incorrectos."

    if fila["estado"] != "activo":
        return None, "El usuario no se encuentra activo."

    if not check_password_hash(fila["password_hash"], contrasena):
        return None, "Usuario o contrasena incorrectos."

    registrar_acceso(fila["id"])
    return obtener_usuario_por_id(fila["id"]), None


def registrar_acceso(usuario_id):
    ejecutar(
        "UPDATE usuarios SET ultimo_acceso = %s WHERE id = %s",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario_id),
    )


def crear_usuario_si_no_existe(usuario, contrasena, nombre, correo, documento, rol, estado="activo"):
    existente = consultar_uno("SELECT id FROM usuarios WHERE usuario = %s", (usuario,))
    if existente:
        return False

    ejecutar(
        """
        INSERT INTO usuarios (usuario, password_hash, nombre, correo, documento, rol, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            usuario,
            generate_password_hash(contrasena),
            nombre,
            correo,
            documento,
            rol,
            estado,
        ),
    )
    return True


def preparar_usuarios_iniciales():
    admin_password = os.environ.get("AUTOMAN_ADMIN_PASSWORD", "admin123")
    almacen_password = os.environ.get("AUTOMAN_ALMACEN_PASSWORD", "almacen123")

    creados = []
    if crear_usuario_si_no_existe(
        usuario=os.environ.get("AUTOMAN_ADMIN_USER", "admin"),
        contrasena=admin_password,
        nombre="Administrador AUTOMAN",
        correo="admin@automan.local",
        documento="00000000",
        rol="ADMIN",
    ):
        creados.append(("admin", admin_password))

    if crear_usuario_si_no_existe(
        usuario=os.environ.get("AUTOMAN_ALMACEN_USER", "almacen"),
        contrasena=almacen_password,
        nombre="Operador de almacen",
        correo="almacen@automan.local",
        documento="11111111",
        rol="ALMACEN",
    ):
        creados.append(("almacen", almacen_password))

    return creados
