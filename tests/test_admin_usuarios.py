import unittest
from unittest.mock import patch

from admin_usuariosAD import cambiar_password_usuario, editar_usuario


USUARIO_ADMIN = {
    "id": 1,
    "usuario": "admin",
    "nombre": "Administrador AUTOMAN",
    "correo": "admin@automan.local",
    "documento": "00000000",
    "rol": "ADMIN",
    "estado": "activo",
    "ultimo_acceso": None,
}


class GestionUsuariosTests(unittest.TestCase):
    @patch("admin_usuariosAD.obtener_usuario", return_value=USUARIO_ADMIN)
    def test_admin_cannot_deactivate_itself_from_edit_form(self, _obtener):
        datos = {**USUARIO_ADMIN, "estado": "suspendido"}
        correcto, mensaje = editar_usuario(1, datos, administrador_id=1)
        self.assertFalse(correcto)
        self.assertIn("propia cuenta", mensaje)

    def test_password_confirmation_must_match(self):
        correcto, mensaje = cambiar_password_usuario(2, "segura123", "diferente123")
        self.assertFalse(correcto)
        self.assertIn("no coinciden", mensaje)


if __name__ == "__main__":
    unittest.main()
