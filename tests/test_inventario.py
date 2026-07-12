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

    @patch("inventario_productosAD.consultar_uno", return_value={"id": 1, "stock_actual": Decimal("3"), "ajustes": 1})
    def test_product_with_stock_history_cannot_be_deleted(self, _consultar):
        correcto, mensaje = eliminar_producto(1)
        self.assertFalse(correcto)
        self.assertIn("historial", mensaje)

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

    def test_product_summary_tracks_stock_states(self):
        productos = [
            {**PRODUCTO_ACEITE, "stock_actual": Decimal("0.000"), "stock_minimo": Decimal("2.000")},
            {**PRODUCTO_ACEITE, "id": 2, "stock_actual": Decimal("1.000"), "stock_minimo": Decimal("2.000")},
            {**PRODUCTO_ACEITE, "id": 3, "stock_actual": Decimal("8.000"), "stock_minimo": Decimal("2.000")},
        ]
        resumen = resumen_productos(productos)
        self.assertEqual(resumen["con_stock"], 2)
        self.assertEqual(resumen["sin_stock"], 1)
        self.assertEqual(resumen["bajo_stock"], 1)


if __name__ == "__main__":
    unittest.main()
