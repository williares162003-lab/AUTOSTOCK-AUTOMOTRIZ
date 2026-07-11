# Autostock Automotriz

Sistema de gestion de almacen e inventario para un negocio automotriz.

## Estructura del proyecto

La organizacion sigue el estilo de la intranet CCPL, adaptada a Django y con nombres en espanol:

```text
autostock-automotriz/
  aplicaciones/
    inicio/
      management/commands/
      migrations/
      forms.py
      urls.py
      views.py
  configuracion/
    settings.py
    urls.py
    wsgi.py
  plantillas/
    admin/
      panel.html
    almacen/
    base.html
    login.html
  estaticos/
    css/
      admin/
      almacen/
      base.css
      login.css
    imagenes/
    js/
      admin/
      app.js
  base_datos/
  requirements.txt
  manage.py
```

## Desarrollo local

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py bootstrap_users
.venv\Scripts\python manage.py runserver
```

El comando `bootstrap_users` crea:

- `admin`: administrador y superusuario.
- `almacen`: operador para gestionar el almacen desde el sistema.

Si no defines contrasenas, el comando genera una temporal y la muestra una sola vez.

## Variables de entorno

Usa `.env.example` como referencia. No subas `.env`, bases de datos locales ni claves reales al repositorio.
