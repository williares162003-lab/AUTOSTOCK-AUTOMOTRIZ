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
    js/
      app.js
  tests/
```

## Desarrollo local

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py init-db
.venv\Scripts\python app.py
```

Usuarios iniciales de desarrollo:

- `admin` / `admin123`
- `almacen` / `almacen123`

En produccion define las contrasenas con variables de entorno antes de ejecutar `init-db`.

## Variables de entorno

Usa `.env.example` como referencia. No subas `.env`, bases SQLite locales ni credenciales reales.

## Pruebas

```bash
.venv\Scripts\python -m unittest
```
