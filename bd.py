import os
import re
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def configuracion_bd(incluir_base=True):
    configuracion = {
        "host": os.environ.get("DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
    }
    if incluir_base:
        configuracion["database"] = os.environ.get("DB_NAME", "automan_almacen")
    return configuracion


def _crear_base_si_no_existe():
    nombre_bd = os.environ.get("DB_NAME", "automan_almacen")
    if not re.fullmatch(r"[A-Za-z0-9_$]+", nombre_bd):
        raise ValueError("DB_NAME contiene caracteres no permitidos.")

    conexion = pymysql.connect(**configuracion_bd(incluir_base=False))
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{nombre_bd}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conexion.commit()
    finally:
        conexion.close()


def obtener_conexion():
    try:
        return pymysql.connect(**configuracion_bd())
    except pymysql.OperationalError as error:
        if error.args and error.args[0] == 1049:
            _crear_base_si_no_existe()
            return pymysql.connect(**configuracion_bd())
        raise


def inicializar_base_datos(reset=False):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if reset:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                cursor.execute("DROP TABLE IF EXISTS presentaciones_producto")
                cursor.execute("DROP TABLE IF EXISTS productos")
                cursor.execute("DROP TABLE IF EXISTS categorias")
                cursor.execute("DROP TABLE IF EXISTS unidades_medida")
                cursor.execute("DROP TABLE IF EXISTS tipos_producto")
                cursor.execute("DROP TABLE IF EXISTS movimientos")
                cursor.execute("DROP TABLE IF EXISTS usuarios")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            contenido = SCHEMA_PATH.read_text(encoding="utf-8")
            for sentencia in contenido.split(";"):
                if sentencia.strip():
                    cursor.execute(sentencia)
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def consultar_uno(sql, parametros=()):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchone()
    finally:
        conexion.close()


def consultar_todos(sql, parametros=()):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
    finally:
        conexion.close()


def ejecutar(sql, parametros=()):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            ultimo_id = cursor.lastrowid
        conexion.commit()
        return ultimo_id
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def ejecutar_transaccion(operacion):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            resultado = operacion(cursor)
        conexion.commit()
        return resultado
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
