import unittest
from unittest.mock import patch

from app import app, ejecutar_comando
from helpers import nav_items


USUARIO_PRUEBA = {
    "id": 1,
    "usuario": "admin",
    "nombre": "Administrador AUTOMAN",
    "correo": "admin@automan.local",
    "documento": "00000000",
    "rol": "ADMIN",
    "estado": "activo",
    "ultimo_acceso": None,
}

USUARIO_ALMACEN = {
    **USUARIO_PRUEBA,
    "id": 2,
    "usuario": "almacen",
    "nombre": "Operador de almacen",
    "correo": "almacen@automan.local",
    "rol": "ALMACEN",
}

RESUMEN_USUARIOS = {"total": 2, "activos": 2, "inactivos": 0, "suspendidos": 0}


class AutomanAppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = app.test_client()

    def test_login_page_loads(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AUTOMAN", response.data)
        self.assertNotIn(b"Atlantica", response.data)

    @patch("app.obtener_serie_movimientos", return_value=[])
    @patch("app.obtener_movimientos_recientes", return_value=[])
    @patch("app.obtener_resumen_dashboard", return_value={"productos": 0, "entradas_mes": 0, "salidas_mes": 0, "alertas_stock": 0, "usuarios_activos": 2})
    @patch("app.autenticar_usuario", return_value=(USUARIO_PRUEBA, None))
    def test_user_can_login_and_open_dashboard(self, _autenticar, _resumen, _movimientos, _serie):
        response = self.client.post(
            "/login",
            data={"usuario": "admin", "contrasena": "admin123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)

    def test_dashboard_api_requires_login(self):
        response = self.client.get("/api/dashboard/resumen")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    @patch("app.obtener_resumen_dashboard", return_value={"productos": 0, "entradas_mes": 0, "salidas_mes": 0, "alertas_stock": 0, "usuarios_activos": 2})
    def test_dashboard_api_returns_summary_after_login(self, _resumen):
        with self.client.session_transaction() as sesion:
            sesion["usuario"] = USUARIO_PRUEBA
        response = self.client.get("/api/dashboard/resumen")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["usuarios_activos"], 2)

    def test_almacen_cannot_open_user_management(self):
        with self.client.session_transaction() as sesion:
            sesion["usuario"] = USUARIO_ALMACEN
        response = self.client.get("/sistema/usuarios")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.location)

    def test_almacen_nav_keeps_operational_sections_only(self):
        labels = [item["label"] for item in nav_items(USUARIO_ALMACEN)]
        self.assertEqual(labels, ["Dashboard", "Inventario", "Movimientos", "Reportes"])

    def test_admin_nav_has_users_without_permissions_screen(self):
        sistema = nav_items(USUARIO_PRUEBA)[-1]
        self.assertEqual(sistema["label"], "Sistema")
        self.assertEqual([item["label"] for item in sistema["children"]], ["Usuarios"])

    @patch("app.resumen_usuarios", return_value=RESUMEN_USUARIOS)
    @patch("app.listar_usuarios", return_value=[USUARIO_PRUEBA, USUARIO_ALMACEN])
    def test_admin_can_open_user_management(self, _listar, _resumen):
        with self.client.session_transaction() as sesion:
            sesion["usuario"] = USUARIO_PRUEBA
        response = self.client.get("/sistema/usuarios")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nuevo usuario", response.data)
        self.assertIn(b"Cambiar contrasena", response.data)

    @patch("app.crear_usuario_ad", return_value=(True, "Usuario creado correctamente."))
    def test_admin_can_submit_new_user(self, crear_usuario):
        with self.client.session_transaction() as sesion:
            sesion["usuario"] = USUARIO_PRUEBA
            sesion["_csrf_token"] = "csrf-prueba"
        response = self.client.post(
            "/sistema/usuarios/crear",
            data={
                "csrf_token": "csrf-prueba",
                "usuario": "nuevo",
                "nombre": "Nuevo usuario",
                "correo": "nuevo@automan.local",
                "documento": "22222222",
                "rol": "ALMACEN",
                "estado": "activo",
                "contrasena": "segura123",
                "confirmar_contrasena": "segura123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/sistema/usuarios", response.location)
        crear_usuario.assert_called_once()

    @patch("app.crear_usuario_ad")
    def test_user_form_rejects_invalid_csrf(self, crear_usuario):
        with self.client.session_transaction() as sesion:
            sesion["usuario"] = USUARIO_PRUEBA
            sesion["_csrf_token"] = "csrf-correcto"
        response = self.client.post(
            "/sistema/usuarios/crear",
            data={"csrf_token": "csrf-incorrecto"},
        )
        self.assertEqual(response.status_code, 302)
        crear_usuario.assert_not_called()

    @patch("app.limpiar_almacen")
    def test_clean_warehouse_command_requires_confirmation(self, limpiar):
        with patch("sys.argv", ["app.py", "limpiar-almacen"]):
            self.assertTrue(ejecutar_comando())
        limpiar.assert_not_called()

    @patch("app.preparar_usuarios_iniciales")
    @patch("app.limpiar_almacen")
    @patch("app.inicializar_base_datos")
    def test_clean_warehouse_command_runs_after_confirmation(
        self, inicializar_bd, limpiar, preparar_usuarios
    ):
        with patch("sys.argv", ["app.py", "limpiar-almacen", "--confirmar"]):
            self.assertTrue(ejecutar_comando())
        inicializar_bd.assert_called_once_with(reset=False)
        limpiar.assert_called_once()
        preparar_usuarios.assert_called_once()


if __name__ == "__main__":
    unittest.main()
