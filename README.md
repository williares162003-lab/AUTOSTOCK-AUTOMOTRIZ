# AUTOMAN Almacen

Sistema de gestion de almacen e inventario para **AUTOMAN Chiclayo E.I.R.L.**

## Estructura del proyecto

La organizacion sigue el estilo del proyecto Intranet CCPL: Flask como entrada principal, rutas y APIs en `app.py`, y funciones de datos/reglas en archivos `AD`.

```text
autostock-automotriz/
  app.py
  bd.py
  helpers.py
  loginAD.py
  admin_dashboardAD.py
  admin_usuariosAD.py
  database/
    schema.sql
    README.md
  pythonanywhere_wsgi.py.example
  templates/
    base.html
    login.html
    admin/
      dashboard.html
      usuarios.html
  static/
    css/
      base.css
      login.css
      admin/
        dashboard.css
        usuarios.css
  tests/
```

## Desarrollo local

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py init-db
.venv\Scripts\python app.py
```

Antes de inicializar, inicia MySQL desde XAMPP. La configuracion local por defecto
es `127.0.0.1:3306`, usuario `root`, sin contrasena y base `automan_almacen`.
Puedes cambiarla con las variables `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`
y `DB_NAME`.

Usuarios iniciales de desarrollo:

- `admin` / `admin123`
- `almacen` / `almacen123`

En produccion define las contrasenas con variables de entorno antes de ejecutar `init-db`.

## Variables de entorno

Configura las variables `AUTOMAN_SECRET_KEY`,
`AUTOMAN_ADMIN_USER`, `AUTOMAN_ADMIN_PASSWORD`, `AUTOMAN_ALMACEN_USER` y
`AUTOMAN_ALMACEN_PASSWORD` segun el entorno. Las credenciales MySQL usan las
variables `DB_*` indicadas arriba. No subas `.env` ni credenciales reales.

## PythonAnywhere

Usa `pythonanywhere_wsgi.py.example` como guia para el archivo WSGI del sitio.
Reemplaza `TU_USUARIO`, la contrasena y la clave secreta directamente en el WSGI
privado de PythonAnywhere; ese archivo real no se sube al repositorio.

## Pruebas

```bash
.venv\Scripts\python -m unittest
```
