import unittest
from unittest.mock import patch

from app import app


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


class AutomanAppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = app.test_client()

    def test_login_page_loads(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AUTOMAN", response.data)
        self.assertNotIn(b"Atlantica", response.data)

    @patch("app.autenticar_usuario", return_value=(USUARIO_PRUEBA, None))
    def test_user_can_login_and_open_dashboard(self, _autenticar):
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

    def test_dashboard_api_returns_summary_after_login(self):
        with self.client.session_transaction() as sesion:
            sesion["usuario"] = USUARIO_PRUEBA
        response = self.client.get("/api/dashboard/resumen")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["usuarios_activos"], 2)


if __name__ == "__main__":
    unittest.main()
