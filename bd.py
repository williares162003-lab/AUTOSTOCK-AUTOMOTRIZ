import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get("AUTOMAN_DATABASE", BASE_DIR / "database" / "automan.sqlite3"))
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def obtener_conexion():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(DATABASE_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_base_datos(reset=False):
    if reset and DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    conexion = obtener_conexion()
    try:
        with SCHEMA_PATH.open("r", encoding="utf-8") as archivo:
            conexion.executescript(archivo.read())
        conexion.commit()
    finally:
        conexion.close()


def consultar_uno(sql, parametros=()):
    conexion = obtener_conexion()
    try:
        return conexion.execute(sql, parametros).fetchone()
    finally:
        conexion.close()


def consultar_todos(sql, parametros=()):
    conexion = obtener_conexion()
    try:
        return conexion.execute(sql, parametros).fetchall()
    finally:
        conexion.close()


def ejecutar(sql, parametros=()):
    conexion = obtener_conexion()
    try:
        cursor = conexion.execute(sql, parametros)
        conexion.commit()
        return cursor.lastrowid
    finally:
        conexion.close()
