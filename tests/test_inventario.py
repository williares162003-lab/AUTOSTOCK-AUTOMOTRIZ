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
    listar_productos,
    preparar_categorias_generales,
    resumen_productos,
)
from movimientos_entradasAD import abrir_balde, abrir_caja, registrar_entrada
from movimientos_kardexAD import listar_movimientos_kardex_con_errores
from movimientos_salidasAD import anular_salida, listar_vehiculos, registrar_salida
from reportesAD import normalizar_filtros_reportes
from tests.test_app import USUARIO_ALMACEN


AREAS = [{"id": 1, "nombre": "Mecanica"}, {"id": 2, "nombre": "Pintura"}, {"id": 3, "nombre": "General"}]
TIPOS = [
    {"id": 1, "nombre": "Repuesto", "area_id": 1, "area": "Mecanica"},
    {"id": 2, "nombre": "Lubricante", "area_id": 1, "area": "Mecanica"},
]
CATEGORIAS = [
    {"id": 1, "nombre": "Sin clasificar", "tipo_id": 1, "tipo": "Repuesto", "area_id": 1, "area": "Mecanica"},
    {"id": 2, "nombre": "Amortiguador", "tipo_id": 1, "tipo": "Repuesto", "area_id": 1, "area": "Mecanica"},
    {"id": 3, "nombre": "Raqueta limpia parabrisas", "tipo_id": 1, "tipo": "Repuesto", "area_id": 1, "area": "Mecanica"},
    {"id": 14, "nombre": "Aceite de motor", "tipo_id": 2, "tipo": "Lubricante", "area_id": 1, "area": "Mecanica"},
]
UNIDADES = [
    {"id": 1, "nombre": "Unidad", "abreviatura": "und", "permite_decimal": 0},
    {"id": 3, "nombre": "Galon", "abreviatura": "gal", "permite_decimal": 1},
]
PRODUCTO_ACEITE = {
    "id": 1,
    "nombre": "Aceite 20W50",
    "codigo": None,
    "marca": None,
    "descripcion": None,
    "stock_actual": Decimal("10.000"),
    "stock_suelto": Decimal("8.000"),
    "stock_balde_abierto": Decimal("2.000"),
    "baldes_abiertos": Decimal("1.000"),
    "stock_baldes_cerrados": Decimal("1.000"),
    "stock_cilindro_abierto": Decimal("0.000"),
    "cilindros_abiertos": Decimal("0.000"),
    "stock_cilindros_cerrados": Decimal("0.000"),
    "litros_por_cilindro": Decimal("0.000"),
    "litros_por_galon": Decimal("0.000"),
    "stock_cajas_cerradas": Decimal("0.000"),
    "unidades_por_caja": Decimal("0.000"),
    "stock_minimo": Decimal("2.000"),
    "observaciones": None,
    "tipo_id": 2,
    "tipo": "Lubricante",
    "area_id": 1,
    "area": "Mecanica",
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

    @patch("app.listar_areas", return_value=AREAS)
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
    def test_almacen_can_open_products(self, _productos, _resumen, _tipos, _categorias, _unidades, _ajustes, _areas):
        response = self.client.get("/inventario/productos")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"Balde", response.data)
        self.assertIn(b"Con stock", response.data)
        self.assertIn(b"Mecanica", response.data)
        self.assertIn(b"Disponible", response.data)
        self.assertIn(b"Usado del balde", response.data)
        self.assertIn(b"Codigo", response.data)
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
    def test_gallon_initial_stock_requires_liters_per_gallon(self, consultar_uno):
        consultar_uno.side_effect = [
            {"id": 14},
            {"id": 3, "permite_decimal": 1, "abreviatura": "gal"},
        ]
        datos = MultiDict(
            [
                ("nombre", "Aceite 5W30"),
                ("tipo_id", "2"),
                ("categoria_id", "14"),
                ("unidad_base_id", "3"),
                ("stock_actual", "2"),
                ("stock_minimo", "0"),
            ]
        )
        correcto, mensaje = crear_producto(datos, usuario_id=2)
        self.assertFalse(correcto)
        self.assertIn("litros", mensaje)

    @patch("inventario_productosAD.ejecutar_transaccion")
    @patch("inventario_productosAD.consultar_uno")
    def test_gallon_initial_stock_is_saved_as_liters(self, consultar_uno, ejecutar_transaccion):
        consultar_uno.side_effect = [
            {"id": 14},
            {"id": 3, "permite_decimal": 1, "abreviatura": "gal"},
            None,
        ]
        ejecuciones = []

        class CursorFalso:
            lastrowid = 12

            def execute(self, sql, parametros=()):
                ejecuciones.append((sql, parametros))

        ejecutar_transaccion.side_effect = lambda operacion: operacion(CursorFalso())
        datos = MultiDict(
            [
                ("nombre", "Aceite 5W30"),
                ("tipo_id", "2"),
                ("categoria_id", "14"),
                ("unidad_base_id", "3"),
                ("stock_actual", "2"),
                ("litros_por_galon", "5"),
                ("stock_minimo", "0"),
            ]
        )

        correcto, mensaje = crear_producto(datos, usuario_id=2)

        self.assertTrue(correcto)
        self.assertIn("registrado", mensaje)
        insert_producto = next(sql_param for sql_param in ejecuciones if "INSERT INTO productos" in sql_param[0])
        parametros = insert_producto[1]
        self.assertIn(Decimal("10.000"), parametros)
        self.assertIn(Decimal("5.000"), parametros)

    @patch("inventario_productosAD.ejecutar_transaccion")
    @patch("inventario_productosAD.consultar_todos")
    @patch("inventario_productosAD.consultar_uno")
    def test_product_allows_same_code_with_different_presentation(
        self, consultar_uno, consultar_todos, ejecutar_transaccion
    ):
        consultar_uno.side_effect = [
            {"id": 14},
            {"id": 3, "permite_decimal": 1},
        ]
        consultar_todos.side_effect = [
            [{"id": 9, "nombre": "Ultrabase 7000", "marca": "Sherwin Williams"}],
            [{"producto_id": 9, "nombre": "1 litro", "factor": Decimal("1.000")}],
        ]
        datos = MultiDict(
            [
                ("nombre", "Ultrabase 7000"),
                ("codigo", "UB-7000"),
                ("tipo_id", "2"),
                ("categoria_id", "14"),
                ("marca", "Sherwin Williams"),
                ("unidad_base_id", "3"),
                ("stock_actual", "0"),
                ("stock_minimo", "0"),
                ("presentacion_nombre", "1/4 litro"),
                ("presentacion_factor", "0.250"),
            ]
        )
        correcto, mensaje = crear_producto(datos, usuario_id=2)
        self.assertTrue(correcto)
        self.assertIn("registrado", mensaje)
        ejecutar_transaccion.assert_called_once()

    @patch("inventario_productosAD.ejecutar_transaccion")
    @patch("inventario_productosAD.consultar_todos")
    @patch("inventario_productosAD.consultar_uno")
    def test_product_rejects_same_code_and_same_presentation(
        self, consultar_uno, consultar_todos, ejecutar_transaccion
    ):
        consultar_uno.side_effect = [
            {"id": 14},
            {"id": 3, "permite_decimal": 1},
        ]
        consultar_todos.side_effect = [
            [{"id": 9, "nombre": "Ultrabase 7000", "marca": "Sherwin Williams"}],
            [{"producto_id": 9, "nombre": "1/4 litro", "factor": Decimal("0.250")}],
        ]
        datos = MultiDict(
            [
                ("nombre", "Ultrabase 7000"),
                ("codigo", "UB-7000"),
                ("tipo_id", "2"),
                ("categoria_id", "14"),
                ("marca", "Sherwin Williams"),
                ("unidad_base_id", "3"),
                ("stock_actual", "0"),
                ("stock_minimo", "0"),
                ("presentacion_nombre", "1/4 litro"),
                ("presentacion_factor", "0.250"),
            ]
        )
        correcto, mensaje = crear_producto(datos, usuario_id=2)
        self.assertFalse(correcto)
        self.assertIn("codigo, nombre y presentacion", mensaje)
        ejecutar_transaccion.assert_not_called()

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

    @patch("inventario_productosAD.consultar_todos")
    def test_product_list_calculates_open_cylinder_available_liters(self, consultar):
        consultar.side_effect = [
            [
                {
                    **PRODUCTO_ACEITE,
                    "stock_actual": Decimal("0.000"),
                    "stock_suelto": Decimal("0.000"),
                    "stock_cilindro_abierto": Decimal("0.000"),
                    "cilindros_abiertos": Decimal("1.000"),
                    "stock_cilindros_cerrados": Decimal("0.000"),
                    "litros_por_cilindro": Decimal("208.000"),
                }
            ],
            [],
        ]

        producto = listar_productos()[0]

        self.assertEqual(producto["stock_cilindro_disponible"], Decimal("208.000"))
        self.assertEqual(producto["stock_total"], Decimal("208.000"))

    @patch(
        "inventario_productosAD.consultar_uno",
        return_value={
            "id": 1,
            "stock_actual": Decimal("3"),
            "stock_suelto": Decimal("3"),
            "stock_balde_abierto": Decimal("0"),
            "baldes_abiertos": Decimal("0"),
            "stock_baldes_cerrados": Decimal("0"),
            "stock_cilindro_abierto": Decimal("0"),
            "cilindros_abiertos": Decimal("0"),
            "stock_cilindros_cerrados": Decimal("0"),
            "stock_cajas_cerradas": Decimal("0"),
            "unidades_por_caja": Decimal("0"),
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
            "stock_cilindro_abierto": Decimal("0"),
            "cilindros_abiertos": Decimal("0"),
            "stock_cilindros_cerrados": Decimal("0"),
            "stock_cajas_cerradas": Decimal("0"),
            "unidades_por_caja": Decimal("0"),
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

    @patch("app.listar_areas", return_value=AREAS)
    @patch("app.listar_tipos", return_value=TIPOS)
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    def test_almacen_can_manage_types_and_categories(self, _categorias, _tipos, _areas):
        response = self.client.get("/inventario/categorias")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nuevo tipo", response.data)
        self.assertIn(b"Nueva categoria", response.data)
        self.assertIn(b"Mecanica", response.data)
        self.assertIn(b"General", response.data)
        self.assertNotIn(b"Editar categoria", response.data)

    @patch("app.listar_areas", return_value=AREAS)
    @patch("app.listar_tipos", return_value=TIPOS)
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    def test_category_type_filter_is_applied_by_server(self, _categorias, _tipos, _areas):
        response = self.client.get("/inventario/categorias?tipo_id=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sin clasificar", response.data)
        self.assertNotIn(b'data-category-name="Aceite de motor"', response.data)
        self.assertIn(b'<option value="Aceite de motor" data-tipos="2"', response.data)
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

    @patch("app.listar_areas", return_value=AREAS)
    @patch("app.resumen_entradas", return_value={"total": 0, "hoy": 0, "mes": 0, "productos": 0})
    @patch("app.listar_aperturas_balde", return_value=[])
    @patch("app.listar_entradas", return_value=[])
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    @patch("app.listar_productos", return_value=[PRODUCTO_ACEITE])
    def test_almacen_can_open_entries(self, _productos, _categorias, _entradas, _aperturas, _resumen, _areas):
        response = self.client.get("/movimientos/entradas")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nueva entrada", response.data)
        self.assertIn(b"Abrir balde", response.data)
        self.assertIn(b"Abrir cilindro", response.data)
        self.assertIn(b"Abrir caja", response.data)
        self.assertIn(b"Mecanica", response.data)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"Raqueta limpia parabrisas", response.data)
        self.assertIn(b"Litros por galon/envase", response.data)

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

    def test_open_box_requires_product(self):
        correcto, mensaje = abrir_caja(
            {"producto_id": ""},
            usuario_id=2,
        )
        self.assertFalse(correcto)
        self.assertIn("producto", mensaje)

    @patch("app.listar_areas", return_value=AREAS)
    @patch("app.resumen_salidas", return_value={"total": 0, "hoy": 0, "mes": 0, "vehiculos": 0})
    @patch("app.listar_salidas", return_value=[])
    @patch("app.listar_vehiculos", return_value=[{"id": 1, "placa": "ABC-123", "modelo": "Toyota Yaris"}])
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    @patch("app.listar_productos", return_value=[PRODUCTO_ACEITE])
    def test_almacen_can_open_outputs(self, _productos, _categorias, _vehiculos, _salidas, _resumen, _areas):
        response = self.client.get("/movimientos/salidas")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nueva salida", response.data)
        self.assertIn(b"ABC-123", response.data)
        self.assertIn(b"Mecanica", response.data)
        self.assertIn(b"Destino", response.data)
        self.assertIn(b"Salida por destino", response.data)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"Sale de", response.data)
        self.assertIn(b"data-quantity-hint", response.data)
        self.assertIn(b"data-gallon-fraction", response.data)
        self.assertNotIn(b"data-gallon-value", response.data)

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
    @patch("app.listar_categorias", return_value=CATEGORIAS)
    @patch("app.listar_tipos", return_value=TIPOS)
    @patch("app.listar_areas", return_value=AREAS)
    @patch("app.listar_productos", return_value=[PRODUCTO_ACEITE])
    def test_almacen_can_open_kardex(
        self,
        _productos,
        _areas,
        _tipos,
        _categorias,
        _movimientos,
        _producto,
        _resumen,
    ):
        response = self.client.get("/movimientos/kardex?producto_id=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Kardex", response.data)
        self.assertIn(b"Aceite 20W50", response.data)
        self.assertIn(b"Compra", response.data)
        self.assertIn(b"Area", response.data)
        self.assertIn(b"Categoria", response.data)
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
                "cilindros_cerrados": Decimal("0.000"),
                "cilindros_en_uso": Decimal("0.000"),
                "cajas_cerradas": Decimal("0.000"),
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
            "errores_reporte": [],
            "stock_critico": [],
            "movimientos_dia": [{"fecha": "2026-07-12", "entradas": 2, "salidas": 1, "entradas_pct": 100, "salidas_pct": 50}],
            "top_salidas": [{"nombre": "Aceite 20W50", "marca": None, "categoria": "Aceite de motor", "cantidad": Decimal("1.000"), "abreviatura": "gal", "movimientos": 1}],
            "salidas_vehiculos": [],
            "destinos_periodo": [
                {
                    "placa": "ABC-123",
                    "modelo": "Toyota Yaris",
                    "salidas": 1,
                    "productos": 1,
                    "ultimo_movimiento": "2026-07-12 10:00:00",
                }
            ],
            "salidas_agrupadas": [
                {
                    "fecha": "2026-07-12",
                    "total_items": 1,
                    "grupos": [
                        {
                            "placa": "ABC-123",
                            "modelo": "Toyota Yaris",
                            "total_items": 1,
                            "salidas": [
                                {
                                    "id": 1,
                                    "hora": "10:00",
                                    "trabajador": "Juan Perez",
                                    "usuario": "William",
                                    "items": [
                                        {
                                            "producto": "Aceite 20W50",
                                            "marca": None,
                                            "cantidad": Decimal("1.000"),
                                            "abreviatura": "gal",
                                            "origen_texto": "Stock suelto",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
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
        self.assertIn(b"Destinos del periodo", response.data)
        self.assertIn(b"Salidas por dia y destino", response.data)
        self.assertIn(b"ABC-123", response.data)
        self.assertIn(b"10:00", response.data)
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
        self.assertIn("Cilindro abierto%%", sql)
        self.assertIn("Cilindro terminado%%", sql)

    @patch("movimientos_kardexAD.consultar_todos", return_value=[])
    def test_kardex_can_filter_by_product_family(self, consultar):
        movimientos, errores = listar_movimientos_kardex_con_errores(
            {"tipo": "entrada", "area_id": "2", "tipo_id": "8", "categoria_id": "13"}
        )
        self.assertEqual(movimientos, [])
        self.assertEqual(errores, [])
        sql = consultar.call_args.args[0]
        parametros = consultar.call_args.args[1]
        self.assertIn("p.tipo_id IN", sql)
        self.assertIn("p.tipo_id = %s", sql)
        self.assertIn("p.categoria_id = %s", sql)
        self.assertEqual(parametros, (2, 8, 13))

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

    @patch("app.anular_salida_ad", return_value=(True, "Salida anulada y stock devuelto correctamente."))
    def test_almacen_can_cancel_output(self, anular):
        response = self.client.post(
            "/movimientos/salidas/7/anular",
            data={"csrf_token": "csrf-inventario", "motivo": "Producto devuelto"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/movimientos/salidas", response.location)
        anular.assert_called_once_with(7, "Producto devuelto", USUARIO_ALMACEN["id"])

    @patch("movimientos_salidasAD.consultar_todos", return_value=[])
    def test_output_destinations_default_to_today(self, consultar):
        listar_vehiculos()
        self.assertEqual(consultar.call_args.args[1], (0,))

    def test_output_cancel_requires_reason(self):
        correcto, mensaje = anular_salida(1, "", usuario_id=2)
        self.assertFalse(correcto)
        self.assertIn("motivo", mensaje)

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
                "stock_cajas_cerradas": Decimal("0.000"),
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
                "stock_cajas_cerradas": Decimal("0.000"),
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
                "stock_cajas_cerradas": Decimal("0.000"),
                "stock_minimo": Decimal("2.000"),
            },
        ]
        resumen = resumen_productos(productos)
        self.assertEqual(resumen["con_stock"], 2)
        self.assertEqual(resumen["sin_stock"], 1)
        self.assertEqual(resumen["bajo_stock"], 1)


if __name__ == "__main__":
    unittest.main()
