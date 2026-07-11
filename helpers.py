from functools import wraps

from flask import redirect, session, url_for


def usuario_actual():
    return session.get("usuario")


def login_requerido(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if not usuario_actual():
            return redirect(url_for("login"))
        return vista(*args, **kwargs)

    return wrapper


def nav_items():
    return [
        {"label": "Dashboard", "icon": "dashboard", "endpoint": "dashboard"},
        {
            "label": "Inventario",
            "icon": "inventory_2",
            "children": [
                {"label": "Productos", "icon": "category", "endpoint": None},
                {"label": "Categorias", "icon": "sell", "endpoint": None},
                {"label": "Marcas", "icon": "bookmark", "endpoint": None},
                {"label": "Ubicaciones", "icon": "shelves", "endpoint": None},
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
        },
    ]


def contexto_base(active_page):
    return {
        "profile": usuario_actual(),
        "nav_items": nav_items(),
        "active_page": active_page,
        "empresa": "AUTOMAN Chiclayo E.I.R.L.",
    }
