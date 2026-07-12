from functools import wraps
from secrets import compare_digest, token_urlsafe

from flask import flash, redirect, request, session, url_for


def usuario_actual():
    return session.get("usuario")


def login_requerido(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if not usuario_actual():
            return redirect(url_for("login"))
        return vista(*args, **kwargs)

    return wrapper


def admin_requerido(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        usuario = usuario_actual()
        if not usuario:
            return redirect(url_for("login"))
        if usuario.get("rol") != "ADMIN":
            flash("No tienes permisos para acceder a esta seccion.", "error")
            return redirect(url_for("dashboard"))
        return vista(*args, **kwargs)

    return wrapper


def token_csrf():
    if "_csrf_token" not in session:
        session["_csrf_token"] = token_urlsafe(32)
    return session["_csrf_token"]


def csrf_requerido(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        token_sesion = session.get("_csrf_token", "")
        token_formulario = request.form.get("csrf_token", "")
        if not token_sesion or not compare_digest(token_sesion, token_formulario):
            flash("La solicitud vencio. Vuelve a intentarlo.", "error")
            destino = request.referrer
            if not destino or not destino.startswith(request.host_url):
                destino = url_for("dashboard")
            return redirect(destino)
        return vista(*args, **kwargs)

    return wrapper


def nav_items(usuario):
    items = [
        {"label": "Dashboard", "icon": "dashboard", "endpoint": "dashboard"},
        {
            "label": "Inventario",
            "icon": "inventory_2",
            "active_pages": ["productos", "categorias"],
            "children": [
                {"label": "Productos", "icon": "inventory_2", "endpoint": "productos"},
                {"label": "Tipos y categorias", "icon": "category", "endpoint": "categorias"},
            ],
        },
        {
            "label": "Movimientos",
            "icon": "sync_alt",
            "children": [
                {"label": "Entradas", "icon": "move_to_inbox", "endpoint": None},
                {"label": "Salidas", "icon": "outbox", "endpoint": None},
                {"label": "Kardex", "icon": "fact_check", "endpoint": None},
            ],
        },
        {"label": "Proveedores", "icon": "local_shipping", "endpoint": None},
        {"label": "Reportes", "icon": "monitoring", "endpoint": None},
    ]

    if usuario and usuario.get("rol") == "ADMIN":
        items.append(
            {
            "label": "Sistema",
            "icon": "settings",
            "endpoint": None,
            "active_prefix": "usuarios",
            "highlight": True,
            "children": [
                {"label": "Usuarios", "icon": "group", "endpoint": "usuarios"},
                {"label": "Permisos", "icon": "lock", "endpoint": None},
            ],
            }
        )

    return items


def contexto_base(active_page):
    usuario = usuario_actual()
    return {
        "profile": usuario,
        "nav_items": nav_items(usuario),
        "active_page": active_page,
        "empresa": "AUTOMAN Chiclayo E.I.R.L.",
        "csrf_token": token_csrf(),
    }
