import os
import re
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def configuracion_bd(incluir_base=True):
    configuracion = {
        "host": os.environ.get("DB_HOST", "localhost"),
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


def _columna_existe(cursor, tabla, columna):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (tabla, columna),
    )
    return cursor.fetchone()["total"] > 0


def _indice_existe(cursor, tabla, indice):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (tabla, indice),
    )
    return cursor.fetchone()["total"] > 0


def _asegurar_columna(cursor, tabla, columna, definicion):
    if not _columna_existe(cursor, tabla, columna):
        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")


def _aplicar_migraciones(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS areas_almacen (
            id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            nombre VARCHAR(80) NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uk_areas_almacen_nombre (nombre)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(
        """
        INSERT IGNORE INTO areas_almacen (id, nombre) VALUES
            (1, 'Mecanica'),
            (2, 'Pintura'),
            (3, 'General')
        """
    )
    _asegurar_columna(
        cursor,
        "tipos_producto",
        "area_id",
        "INT UNSIGNED NULL AFTER id",
    )
    cursor.execute(
        """
        UPDATE tipos_producto
        SET area_id = (SELECT id FROM areas_almacen WHERE LOWER(nombre) = 'mecanica' LIMIT 1)
        WHERE area_id IS NULL
        """
    )
    cursor.execute("ALTER TABLE vehiculos_atendidos MODIFY placa VARCHAR(80) NOT NULL")
    cursor.execute("ALTER TABLE salidas_stock MODIFY placa VARCHAR(80) NOT NULL")
    if _indice_existe(cursor, "tipos_producto", "uk_tipos_producto_nombre"):
        cursor.execute("ALTER TABLE tipos_producto DROP INDEX uk_tipos_producto_nombre")
    if not _indice_existe(cursor, "tipos_producto", "uk_tipos_producto_area_nombre"):
        cursor.execute(
            "ALTER TABLE tipos_producto ADD UNIQUE KEY uk_tipos_producto_area_nombre (area_id, nombre)"
        )
    cursor.execute(
        """
        INSERT IGNORE INTO tipos_producto (area_id, nombre)
        SELECT id, 'Varios'
        FROM areas_almacen
        WHERE LOWER(nombre) = 'general'
        """
    )
    cursor.execute(
        """
        INSERT IGNORE INTO categorias (tipo_id, nombre)
        SELECT t.id, 'Sin clasificar'
        FROM tipos_producto t
        INNER JOIN areas_almacen a ON a.id = t.area_id
        WHERE LOWER(a.nombre) = 'general'
          AND LOWER(t.nombre) = 'varios'
        """
    )
    _asegurar_columna(
        cursor,
        "productos",
        "codigo",
        "VARCHAR(80) NULL AFTER nombre",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "marca",
        "VARCHAR(100) NULL AFTER categoria_id",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "descripcion",
        "TEXT NULL AFTER marca",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "unidad_base_id",
        "INT UNSIGNED NOT NULL DEFAULT 1 AFTER descripcion",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_actual",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER unidad_base_id",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_minimo",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_actual",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "observaciones",
        "TEXT NULL AFTER stock_minimo",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "creado_por",
        "INT UNSIGNED NULL AFTER observaciones",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "presentacion_id",
        "INT UNSIGNED NULL AFTER producto_id",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "presentacion_nombre",
        "VARCHAR(80) NOT NULL DEFAULT 'Unidad base' AFTER presentacion_id",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "factor",
        "DECIMAL(14,3) NOT NULL DEFAULT 1 AFTER presentacion_nombre",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "cantidad_base",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER cantidad",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "stock_anterior",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER origen_stock",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "stock_nuevo",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_anterior",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "documento",
        "VARCHAR(80) NULL AFTER stock_nuevo",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "motivo",
        "VARCHAR(255) NOT NULL DEFAULT 'Entrada de almacen' AFTER documento",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "usuario_id",
        "INT UNSIGNED NULL AFTER motivo",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "creado_en",
        "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER usuario_id",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_suelto",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_actual",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_balde_abierto",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_suelto",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_baldes_cerrados",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_balde_abierto",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "baldes_abiertos",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_balde_abierto",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_cilindro_abierto",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_baldes_cerrados",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "cilindros_abiertos",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_cilindro_abierto",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_cilindros_cerrados",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER cilindros_abiertos",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "litros_por_cilindro",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_cilindros_cerrados",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "stock_cajas_cerradas",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER litros_por_cilindro",
    )
    _asegurar_columna(
        cursor,
        "productos",
        "unidades_por_caja",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_cajas_cerradas",
    )
    _asegurar_columna(
        cursor,
        "entradas_stock",
        "origen_stock",
        "VARCHAR(30) NOT NULL DEFAULT 'suelto' AFTER cantidad_base",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock_detalle",
        "cantidad_base",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER producto_id",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock_detalle",
        "origen_stock",
        "VARCHAR(30) NOT NULL DEFAULT 'suelto' AFTER cantidad_base",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock_detalle",
        "stock_anterior",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER origen_stock",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock_detalle",
        "stock_nuevo",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_anterior",
    )
    _asegurar_columna(
        cursor,
        "vehiculos_atendidos",
        "modelo",
        "VARCHAR(120) NULL AFTER placa",
    )
    _asegurar_columna(
        cursor,
        "vehiculos_atendidos",
        "ultimo_uso",
        "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER modelo",
    )
    _asegurar_columna(
        cursor,
        "vehiculos_atendidos",
        "creado_en",
        "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER ultimo_uso",
    )
    _asegurar_columna(
        cursor,
        "vehiculos_atendidos",
        "actualizado_en",
        "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER creado_en",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock",
        "vehiculo_id",
        "INT UNSIGNED NULL AFTER id",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock",
        "placa",
        "VARCHAR(20) NULL AFTER vehiculo_id",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock",
        "modelo",
        "VARCHAR(120) NULL AFTER placa",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock",
        "trabajador",
        "VARCHAR(160) NOT NULL DEFAULT 'Sin registrar' AFTER modelo",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock",
        "usuario_id",
        "INT UNSIGNED NULL AFTER trabajador",
    )
    _asegurar_columna(
        cursor,
        "salidas_stock",
        "creado_en",
        "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER usuario_id",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "envase",
        "VARCHAR(20) NOT NULL DEFAULT 'balde' AFTER producto_id",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "tipo",
        "VARCHAR(20) NOT NULL DEFAULT 'apertura' AFTER envase",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "baldes_abiertos",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER tipo",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "contenido_por_balde",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER baldes_abiertos",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "cantidad_base",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER contenido_por_balde",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "stock_baldes_anterior",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER cantidad_base",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "stock_baldes_nuevo",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_baldes_anterior",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "baldes_en_uso_anterior",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_baldes_nuevo",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "baldes_en_uso_nuevo",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER baldes_en_uso_anterior",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "stock_abierto_anterior",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER baldes_en_uso_nuevo",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "stock_abierto_nuevo",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_abierto_anterior",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "stock_anterior",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_abierto_nuevo",
    )
    _asegurar_columna(
        cursor,
        "aperturas_balde",
        "stock_nuevo",
        "DECIMAL(14,3) NOT NULL DEFAULT 0 AFTER stock_anterior",
    )
    cursor.execute(
        """
        UPDATE productos
        SET stock_suelto = stock_actual
        WHERE stock_actual > 0
          AND stock_suelto = 0
          AND stock_balde_abierto = 0
          AND stock_baldes_cerrados = 0
        """
    )
    cursor.execute("UPDATE productos SET stock_actual = stock_suelto WHERE stock_actual <> stock_suelto")


def inicializar_base_datos(reset=False):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if reset:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                cursor.execute("DROP TABLE IF EXISTS ajustes_stock")
                cursor.execute("DROP TABLE IF EXISTS aperturas_balde")
                cursor.execute("DROP TABLE IF EXISTS salidas_stock_detalle")
                cursor.execute("DROP TABLE IF EXISTS salidas_stock")
                cursor.execute("DROP TABLE IF EXISTS vehiculos_atendidos")
                cursor.execute("DROP TABLE IF EXISTS entradas_stock")
                cursor.execute("DROP TABLE IF EXISTS presentaciones_producto")
                cursor.execute("DROP TABLE IF EXISTS productos")
                cursor.execute("DROP TABLE IF EXISTS categorias")
                cursor.execute("DROP TABLE IF EXISTS unidades_medida")
                cursor.execute("DROP TABLE IF EXISTS tipos_producto")
                cursor.execute("DROP TABLE IF EXISTS areas_almacen")
                cursor.execute("DROP TABLE IF EXISTS movimientos")
                cursor.execute("DROP TABLE IF EXISTS usuarios")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            contenido = SCHEMA_PATH.read_text(encoding="utf-8")
            for sentencia in contenido.split(";"):
                if sentencia.strip():
                    cursor.execute(sentencia)
            _aplicar_migraciones(cursor)
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def limpiar_almacen():
    tablas = [
        "ajustes_stock",
        "aperturas_balde",
        "salidas_stock_detalle",
        "salidas_stock",
        "vehiculos_atendidos",
        "entradas_stock",
        "presentaciones_producto",
        "productos",
        "categorias",
        "tipos_producto",
        "movimientos",
    ]
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for tabla in tablas:
                cursor.execute(f"DELETE FROM {tabla}")
                cursor.execute(f"ALTER TABLE {tabla} AUTO_INCREMENT = 1")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
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
