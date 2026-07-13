import unittest
from decimal import Decimal
from unittest.mock import patch

from werkzeug.datastructures import MultiDict

from app import app
from inventario_productosAD import (
    ajustar_stock_producto,
    crear_producto,
    eliminar_categoria,
    eliminar_producto,
    eliminar_tipo,
    preparar_categorias_generales,
    resumen_productos,
)
from movimientos_entradasAD import abrir_balde, registrar_entrada
from movimientos_kardexAD import listar_movimientos_kardex_con_errores
from movimientos_salidasAD import registrar_salida
from reportesAD import normalizar_filtros_reportes
from tests.test_app import USUARIO_ALMACEN


TIPOS = [{"id": 1, "nombre": "Repuesto"}, {"id": 2, "nombre": "Lubricante"}]
CATEGORIAS = [
    {"id": 1, "nombre": "Sin clasificar", "tipo_id": 1, "tipo": "Repuesto"},
    {"id": 14, "nombre": "Aceite de motor", "tipo_id": 2, "tipo": "Lubricante"},
]
UNIDADES = [
    {"id": 1, "nombre": "Unidad", "abreviatura": "und", "permite_decimal": 0},
    {"id": 3, "nombre": "Galon", "abreviatura": "gal", "permite_decimal": 1},
]
PRODUCTO_ACEITE = {
    "id": 1,
    "nombre": "Aceite 20W50",
    "marca": None,
    "descripcion": None,
    "stock_actual": Decimal("10.000"),
    "stock_suelto": Decimal("8.000"),
    "stock_balde_abierto": Decimal("2.000"),
    "baldes_abiertos": Decimal("1.000"),
    "stock_baldes_cerrados": Decimal("1.000"),
    "stock_minimo": Decimal("2.000"),
    "observaciones": None,
    "tipo_id": 2,
    "tipo": "Lubricante",
    "categoria_id": 14,
    "categoria": "Aceite de motor",
    "unidad_base_id": 3,
    "unidad": "Galon",
    "abreviatura": "gal",
    "permite_decimal": 1,
    "presentaciones": [{"id": 1, "producto_id": 1, "nombre": "Balde", "factor": Decimal("5.000")}],
}


class InventarioAppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = app.test_client()
        with self.client.session_transaction() as sesion:
            sesion["usuario"] = USUARIO_ALMACEN
            sesion["_csrf_token"] = "csrf-inventario"

    @patch("app.listar_ajustes_stock", return_value=[])
    @patch("app.listar_unidades", return_value=UNIDADES)
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    @patch("app.listar_tipos", return_value=TIPOS)
    @patch(
        "app.resumen_productos",
        return_value={
            "total": 1,
            "con_stock": 1,
            "sin_stock": 0,
            "repuestos": 0,
            "lubricantes": 1,
            "bajo_stock": 0,
        },
    )
    @patch("app.listar_productos", return_value=[PRODUCTO_ACEITE])
    def test_almacen_can_open_products(self, _productos, _resumen, _tipos, _categorias, _unidades, _ajustes):
        response = self.client.get("/inventario/productos")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"Balde", response.data)
        self.assertIn(b"Con stock", response.data)
        self.assertIn(b"Disponible", response.data)
        self.assertIn(b"Usado del balde", response.data)
        self.assertIn(b"data-view-product", response.data)

    @patch("app.crear_producto_ad", return_value=(True, "Producto registrado correctamente."))
    def test_almacen_can_submit_product(self, crear_producto_ad):
        response = self.client.post(
            "/inventario/productos/crear",
            data={"csrf_token": "csrf-inventario", "nombre": "Aceite 20W50"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/inventario/productos", response.location)
        crear_producto_ad.assert_called_once()

    def test_zero_presentation_factor_is_rejected(self):
        datos = MultiDict(
            [
                ("nombre", "Aceite 20W50"),
                ("tipo_id", "2"),
                ("categoria_id", "14"),
                ("unidad_base_id", "3"),
                ("stock_actual", "10"),
                ("stock_minimo", "2"),
                ("presentacion_nombre", "Balde"),
                ("presentacion_factor", "0"),
            ]
        )
        correcto, mensaje = crear_producto(datos, usuario_id=2)
        self.assertFalse(correcto)
        self.assertIn("mayor que cero", mensaje)

    @patch("inventario_productosAD.consultar_uno")
    def test_unit_products_reject_fractional_stock(self, consultar_uno):
        consultar_uno.side_effect = [
            {"id": 1},
            {"id": 1, "permite_decimal": 0},
        ]
        datos = MultiDict(
            [
                ("nombre", "Pastilla de freno"),
                ("tipo_id", "1"),
                ("categoria_id", "3"),
                ("unidad_base_id", "1"),
                ("stock_actual", "2.5"),
                ("stock_minimo", "1"),
            ]
        )
        correcto, mensaje = crear_producto(datos, usuario_id=2)
        self.assertFalse(correcto)
        self.assertIn("enteras", mensaje)

    def test_stock_adjustment_requires_reason(self):
        correcto, mensaje = ajustar_stock_producto(
            1,
            {"stock_nuevo": "8", "motivo": ""},
            usuario_id=2,
        )
        self.assertFalse(correcto)
        self.assertIn("motivo", mensaje)

    @patch(
        "inventario_productosAD.consultar_uno",
        return_value={
            "id": 1,
            "stock_actual": Decimal("3"),
            "stock_suelto": Decimal("3"),
            "stock_balde_abierto": Decimal("0"),
            "baldes_abiertos": Decimal("0"),
            "stock_baldes_cerrados": Decimal("0"),
        },
    )
    def test_product_with_stock_cannot_be_deleted(self, _consultar):
        correcto, mensaje = eliminar_producto(1)
        self.assertFalse(correcto)
        self.assertIn("stock", mensaje)

    @patch("inventario_productosAD.ejecutar_transaccion")
    @patch(
        "inventario_productosAD.consultar_uno",
        return_value={
            "id": 1,
            "stock_actual": Decimal("0"),
            "stock_suelto": Decimal("0"),
            "stock_balde_abierto": Decimal("0"),
            "baldes_abiertos": Decimal("0"),
            "stock_baldes_cerrados": Decimal("0"),
        },
    )
    def test_product_without_stock_can_be_deleted_with_history_cleanup(self, _consultar, ejecutar_transaccion):
        correcto, mensaje = eliminar_producto(1)
        self.assertTrue(correcto)
        self.assertIn("eliminado", mensaje)
        ejecutar_transaccion.assert_called_once()

    @patch("inventario_productosAD.consultar_uno", return_value={"id": 3, "nombre": "Filtros", "productos": 2})
    def test_category_with_products_cannot_be_deleted(self, _consultar):
        correcto, mensaje = eliminar_categoria(3)
        self.assertFalse(correcto)
        self.assertIn("contiene productos", mensaje)

    @patch(
        "inventario_productosAD.consultar_uno",
        return_value={"id": 1, "nombre": "Sin clasificar", "productos": 0},
    )
    def test_general_category_cannot_be_deleted(self, _consultar):
        correcto, mensaje = eliminar_categoria(1)
        self.assertFalse(correcto)
        self.assertIn("necesaria", mensaje)

    @patch("inventario_productosAD.consultar_uno", return_value={"id": 1, "categorias": 4, "productos": 0})
    def test_type_with_categories_cannot_be_deleted(self, _consultar):
        correcto, mensaje = eliminar_tipo(1)
        self.assertFalse(correcto)
        self.assertIn("contiene categorias", mensaje)

    @patch("app.listar_tipos", return_value=TIPOS)
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    def test_almacen_can_manage_types_and_categories(self, _categorias, _tipos):
        response = self.client.get("/inventario/categorias")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nuevo tipo", response.data)
        self.assertIn(b"Nueva categoria", response.data)
        self.assertNotIn(b"Editar categoria", response.data)

    @patch("app.listar_tipos", return_value=TIPOS)
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    def test_category_type_filter_is_applied_by_server(self, _categorias, _tipos):
        response = self.client.get("/inventario/categorias?tipo_id=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sin clasificar", response.data)
        self.assertNotIn(b'data-category-name="Aceite de motor"', response.data)
        self.assertIn(b'<option value="Aceite de motor" data-tipos="2">', response.data)
        self.assertIn(b'<option value="1" selected>', response.data)

    @patch("app.crear_tipo_ad", return_value=(True, "Tipo de producto creado correctamente."))
    def test_almacen_can_submit_new_type(self, crear_tipo_ad):
        response = self.client.post(
            "/inventario/tipos/crear",
            data={"csrf_token": "csrf-inventario", "nombre": "Consumible"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/inventario/categorias", response.location)
        crear_tipo_ad.assert_called_once()

    @patch("inventario_productosAD.ejecutar")
    def test_general_category_backfill_is_available(self, ejecutar):
        preparar_categorias_generales()
        ejecutar.assert_called_once()
        self.assertIn("Sin clasificar", ejecutar.call_args.args[0])

    @patch("app.resumen_entradas", return_value={"total": 0, "hoy": 0, "mes": 0, "productos": 0})
    @patch("app.listar_aperturas_balde", return_value=[])
    @patch("app.listar_entradas", return_value=[])
    @patch("app.listar_productos", return_value=[PRODUCTO_ACEITE])
    def test_almacen_can_open_entries(self, _productos, _entradas, _aperturas, _resumen):
        response = self.client.get("/movimientos/entradas")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nueva entrada", response.data)
        self.assertIn(b"Abrir balde", response.data)
        self.assertIn(b"Aceite 20W50", response.data)

    @patch("app.registrar_entrada", return_value=(True, "Entrada registrada correctamente."))
    def test_almacen_can_submit_entry(self, registrar):
        response = self.client.post(
            "/movimientos/entradas/crear",
            data={
                "csrf_token": "csrf-inventario",
                "producto_id": "1",
                "presentacion_id": "base",
                "cantidad": "2",
                "motivo": "Compra",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/movimientos/entradas", response.location)
        registrar.assert_called_once()

    def test_entry_rejects_invalid_quantity(self):
        correcto, mensaje = registrar_entrada(
            {"producto_id": "1", "presentacion_id": "base", "cantidad": "0", "motivo": "Compra"},
            usuario_id=2,
        )
        self.assertFalse(correcto)
        self.assertIn("mayor que cero", mensaje)

    def test_open_bucket_requires_product(self):
        correcto, mensaje = abrir_balde(
            {"producto_id": ""},
            usuario_id=2,
        )
        self.assertFalse(correcto)
        self.assertIn("producto", mensaje)

    @patch("app.resumen_salidas", return_value={"total": 0, "hoy": 0, "mes": 0, "vehiculos": 0})
    @patch("app.listar_salidas", return_value=[])
    @patch("app.listar_vehiculos", return_value=[{"id": 1, "placa": "ABC-123", "modelo": "Toyota Yaris"}])
    @patch("app.listar_productos", return_value=[PRODUCTO_ACEITE])
    def test_almacen_can_open_outputs(self, _productos, _vehiculos, _salidas, _resumen):
        response = self.client.get("/movimientos/salidas")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nueva salida", response.data)
        self.assertIn(b"ABC-123", response.data)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"Sale de", response.data)

    @patch("app.resumen_kardex", return_value={"total": 1, "entradas": 1, "salidas": 0, "ajustes": 0, "baldes": 0})
    @patch("app.obtener_producto_kardex", return_value=PRODUCTO_ACEITE)
    @patch(
        "app.listar_movimientos_kardex_con_errores",
        return_value=(
            [
                {
                    "fecha": "2026-07-12 10:00:00",
                    "producto": "Aceite 20W50",
                    "marca": None,
                    "tipo": "Entrada",
                    "tipo_clase": "entrada",
                    "origen": "Stock suelto",
                    "detalle": "Compra",
                    "referencia": "Factura 1",
                    "entrada": Decimal("2.000"),
                    "salida": None,
                    "unidad": "gal",
                    "stock_anterior": Decimal("8.000"),
                    "stock_nuevo": Decimal("10.000"),
                    "usuario": "William",
                }
            ],
            [],
        ),
    )
    @patch("app.listar_productos", return_value=[PRODUCTO_ACEITE])
    def test_almacen_can_open_kardex(self, _productos, _movimientos, _producto, _resumen):
        response = self.client.get("/movimientos/kardex?producto_id=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Kardex", response.data)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"Compra", response.data)
        self.assertIn(b"/movimientos/kardex", response.data)

    @patch(
        "app.obtener_reporte_general",
        return_value={
            "filtros": {"fecha_inicio": "2026-07-01", "fecha_fin": "2026-07-12"},
            "atajos": {
                "hoy": {"inicio": "2026-07-12", "fin": "2026-07-12"},
                "ayer": {"inicio": "2026-07-11", "fin": "2026-07-11"},
                "semana": {"inicio": "2026-07-06", "fin": "2026-07-12"},
                "mes": {"inicio": "2026-07-01", "fin": "2026-07-12"},
            },
            "periodo_es_dia": False,
            "resumen": {
                "productos": 1,
                "con_stock": 1,
                "sin_stock": 0,
                "bajo_stock": 0,
                "baldes_cerrados": Decimal("1.000"),
                "baldes_en_uso": Decimal("0.000"),
                "entradas": 2,
                "productos_entrada": 1,
                "salidas": 1,
                "lineas_salida": 1,
                "productos_salida": 1,
            },
            "actividad": [
                {
                    "fecha": "2026-07-12 10:00:00",
                    "producto": "Aceite 20W50",
                    "marca": None,
                    "tipo": "Salida",
                    "tipo_clase": "salida",
                    "origen": "Stock suelto",
                    "detalle": "ABC-123 / Juan Perez",
                    "entrada": None,
                    "salida": Decimal("1.000"),
                    "unidad": "gal",
                    "usuario": "William",
                }
            ],
            "errores_actividad": [],
            "stock_critico": [],
            "movimientos_dia": [{"fecha": "2026-07-12", "entradas": 2, "salidas": 1, "entradas_pct": 100, "salidas_pct": 50}],
            "top_salidas": [{"nombre": "Aceite 20W50", "marca": None, "categoria": "Aceite de motor", "cantidad": Decimal("1.000"), "abreviatura": "gal", "movimientos": 1}],
            "salidas_vehiculos": [],
            "entradas_recientes": [],
            "stock_tipos": [{"tipo": "Lubricante", "productos": 1, "con_stock": 1, "bajo_stock": 0, "sin_stock": 0}],
            "ajustes_recientes": [],
        },
    )
    def test_almacen_can_open_reports(self, _reporte):
        response = self.client.get("/reportes")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reportes", response.data)
        self.assertIn(b"Actividad del periodo", response.data)
        self.assertIn(b"Hoy", response.data)
        self.assertIn(b"Semana", response.data)
        self.assertIn(b"Exportar CSV", response.data)
        self.assertIn(b"Productos mas retirados", response.data)
        self.assertIn(b"Entradas recientes", response.data)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"/reportes", response.data)

    @patch("app.generar_reporte_csv", return_value=("reporte-automan.csv", "columna\nvalor\n"))
    def test_almacen_can_export_reports_csv(self, generar_csv):
        response = self.client.get("/reportes/exportar?fecha_inicio=2026-07-12&fecha_fin=2026-07-12")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn("attachment; filename=reporte-automan.csv", response.headers["Content-Disposition"])
        self.assertIn("columna", response.get_data(as_text=True))
        generar_csv.assert_called_once()

    def test_reports_default_to_current_day(self):
        filtros = normalizar_filtros_reportes({})
        self.assertEqual(filtros["fecha_inicio"], filtros["fecha_fin"])

    @patch("movimientos_kardexAD.consultar_todos", return_value=[])
    def test_kardex_adjustment_query_escapes_literal_percent(self, consultar):
        movimientos, errores = listar_movimientos_kardex_con_errores({"tipo": "ajuste"})
        self.assertEqual(movimientos, [])
        self.assertEqual(errores, [])
        sql = consultar.call_args.args[0]
        self.assertIn("Entrada:%%", sql)
        self.assertIn("Salida %%", sql)
        self.assertIn("Balde abierto%%", sql)
        self.assertIn("Balde terminado%%", sql)

    @patch("app.registrar_salida", return_value=(True, "Salida registrada correctamente."))
    def test_almacen_can_submit_output(self, registrar):
        response = self.client.post(
            "/movimientos/salidas/crear",
            data={
                "csrf_token": "csrf-inventario",
                "placa": "ABC-123",
                "modelo": "Toyota Yaris",
                "trabajador": "Juan Perez",
                "producto_id": "1",
                "origen_stock": "suelto",
                "cantidad": "2",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/movimientos/salidas", response.location)
        registrar.assert_called_once()

    def test_output_requires_worker(self):
        correcto, mensaje = registrar_salida(
            {"placa": "ABC-123", "trabajador": "", "producto_id": "1", "cantidad": "1"},
            usuario_id=2,
        )
        self.assertFalse(correcto)
        self.assertIn("trabajador", mensaje)

    def test_output_rejects_invalid_quantity(self):
        correcto, mensaje = registrar_salida(
            {"placa": "ABC-123", "trabajador": "Juan Perez", "producto_id": "1", "cantidad": "0"},
            usuario_id=2,
        )
        self.assertFalse(correcto)
        self.assertIn("mayor que cero", mensaje)

    def test_product_summary_tracks_stock_states(self):
        productos = [
            {
                **PRODUCTO_ACEITE,
                "stock_actual": Decimal("0.000"),
                "stock_suelto": Decimal("0.000"),
                "stock_balde_abierto": Decimal("0.000"),
                "baldes_abiertos": Decimal("0.000"),
                "stock_baldes_cerrados": Decimal("0.000"),
                "stock_minimo": Decimal("2.000"),
            },
            {
                **PRODUCTO_ACEITE,
                "id": 2,
                "stock_actual": Decimal("0.000"),
                "stock_suelto": Decimal("0.000"),
                "stock_balde_abierto": Decimal("0.000"),
                "baldes_abiertos": Decimal("1.000"),
                "stock_baldes_cerrados": Decimal("2.000"),
                "stock_minimo": Decimal("2.000"),
            },
            {
                **PRODUCTO_ACEITE,
                "id": 3,
                "stock_actual": Decimal("1.000"),
                "stock_suelto": Decimal("1.000"),
                "stock_balde_abierto": Decimal("0.000"),
                "baldes_abiertos": Decimal("0.000"),
                "stock_baldes_cerrados": Decimal("0.000"),
                "stock_minimo": Decimal("2.000"),
            },
        ]
        resumen = resumen_productos(productos)
        self.assertEqual(resumen["con_stock"], 2)
        self.assertEqual(resumen["sin_stock"], 1)
        self.assertEqual(resumen["bajo_stock"], 1)


if __name__ == "__main__":
    unittest.main()
