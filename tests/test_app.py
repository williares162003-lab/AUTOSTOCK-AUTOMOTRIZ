import os
import tempfile
import unittest
from pathlib import Path


TEMP_DIR = tempfile.TemporaryDirectory()
os.environ["AUTOMAN_DATABASE"] = str(Path(TEMP_DIR.name) / "automan_test.sqlite3")
os.environ["AUTOMAN_SECRET_KEY"] = "test-secret-key"

from app import app, inicializar_sistema  # noqa: E402


class AutomanAppTests(unittest.TestCase):
    def setUp(self):
        inicializar_sistema(reset=True)
        app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = app.test_client()

    def test_login_page_loads(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AUTOMAN", response.data)

    def test_user_can_login_and_open_dashboard(self):
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
        self.client.post("/login", data={"usuario": "almacen", "contrasena": "almacen123"})
        response = self.client.get("/api/dashboard/resumen")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["usuarios_activos"], 2)


if __name__ == "__main__":
    unittest.main()
