import os
import sys

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from admin_dashboardAD import (
    obtener_alertas_dashboard,
    obtener_movimientos_recientes,
    obtener_resumen_dashboard,
    obtener_serie_movimientos,
)
from admin_usuariosAD import (
    cambiar_estado_usuario,
    cambiar_password_usuario,
    crear_usuario as crear_usuario_ad,
    editar_usuario as editar_usuario_ad,
    listar_usuarios,
    obtener_usuario,
    resumen_usuarios,
)
from bd import inicializar_base_datos
from helpers import admin_requerido, contexto_base, csrf_requerido, login_requerido
from inventario_productosAD import (
    crear_categoria as crear_categoria_ad,
    crear_producto as crear_producto_ad,
    editar_categoria as editar_categoria_ad,
    editar_producto as editar_producto_ad,
    listar_categorias,
    listar_productos,
    listar_tipos,
    listar_unidades,
    resumen_productos,
)
from loginAD import autenticar_usuario, preparar_usuarios_iniciales


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("AUTOMAN_SECRET_KEY", "automan-dev-secret-key")


def inicializar_sistema(reset=False):
    inicializar_base_datos(reset=reset)
    return preparar_usuarios_iniciales()


@app.route("/")
def inicio():
    if session.get("usuario"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        contrasena = request.form.get("contrasena", "")
        usuario_validado, error = autenticar_usuario(usuario, contrasena)

        if usuario_validado:
            session["usuario"] = usuario_validado
            flash("Sesion iniciada correctamente.", "success")
            return redirect(url_for("dashboard"))

        flash(error, "error")

    return render_template("login.html", page_title="Iniciar sesion")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesion cerrada.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_requerido
def dashboard():
    contexto = contexto_base("dashboard")
    contexto.update(
        {
            "page_title": "Dashboard",
            "page_subtitle": "Vista operativa del almacen y estado inicial del sistema.",
            "stats": obtener_resumen_dashboard(),
            "alertas": obtener_alertas_dashboard(),
            "movimientos": obtener_movimientos_recientes(),
            "serie_movimientos": obtener_serie_movimientos(),
        }
    )
    return render_template("admin/dashboard.html", **contexto)


@app.route("/sistema/usuarios")
@admin_requerido
def usuarios():
    contexto = contexto_base("usuarios")
    contexto.update(
        {
            "page_title": "Gestion de usuarios",
            "page_subtitle": "Administra el acceso del administrador y del responsable de almacen.",
            "usuarios": listar_usuarios(),
            "resumen": resumen_usuarios(),
        }
    )
    return render_template("admin/usuarios.html", **contexto)


@app.get("/inventario/productos")
@login_requerido
def productos():
    productos_registrados = listar_productos()
    contexto = contexto_base("productos")
    contexto.update(
        {
            "page_title": "Productos",
            "page_subtitle": "Registra los articulos y cantidades encontradas en el almacen.",
            "productos": productos_registrados,
            "resumen": resumen_productos(productos_registrados),
            "tipos": listar_tipos(),
            "categorias": listar_categorias(),
            "unidades": listar_unidades(),
        }
    )
    return render_template("inventario/productos.html", **contexto)


@app.post("/inventario/productos/crear")
@login_requerido
@csrf_requerido
def crear_producto():
    correcto, mensaje = crear_producto_ad(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("productos"))


@app.post("/inventario/productos/<int:producto_id>/editar")
@login_requerido
@csrf_requerido
def editar_producto(producto_id):
    correcto, mensaje = editar_producto_ad(producto_id, request.form)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("productos"))


@app.get("/inventario/categorias")
@login_requerido
def categorias():
    contexto = contexto_base("categorias")
    contexto.update(
        {
            "page_title": "Categorias",
            "page_subtitle": "Organiza los productos por tipo y familia.",
            "categorias": listar_categorias(),
            "tipos": listar_tipos(),
        }
    )
    return render_template("inventario/categorias.html", **contexto)


@app.post("/inventario/categorias/crear")
@login_requerido
@csrf_requerido
def crear_categoria():
    correcto, mensaje = crear_categoria_ad(request.form)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("categorias"))


@app.post("/inventario/categorias/<int:categoria_id>/editar")
@login_requerido
@csrf_requerido
def editar_categoria(categoria_id):
    correcto, mensaje = editar_categoria_ad(categoria_id, request.form)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("categorias"))


@app.post("/sistema/usuarios/crear")
@admin_requerido
@csrf_requerido
def crear_usuario():
    correcto, mensaje = crear_usuario_ad(request.form)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("usuarios"))


@app.post("/sistema/usuarios/<int:usuario_id>/editar")
@admin_requerido
@csrf_requerido
def editar_usuario(usuario_id):
    administrador_id = session["usuario"]["id"]
    correcto, mensaje = editar_usuario_ad(usuario_id, request.form, administrador_id)
    if correcto and usuario_id == administrador_id:
        session["usuario"] = obtener_usuario(usuario_id)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("usuarios"))


@app.post("/sistema/usuarios/<int:usuario_id>/estado")
@admin_requerido
@csrf_requerido
def actualizar_estado_usuario(usuario_id):
    correcto, mensaje = cambiar_estado_usuario(
        usuario_id,
        request.form.get("estado", ""),
        session["usuario"]["id"],
    )
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("usuarios"))


@app.post("/sistema/usuarios/<int:usuario_id>/password")
@admin_requerido
@csrf_requerido
def actualizar_password_usuario(usuario_id):
    correcto, mensaje = cambiar_password_usuario(
        usuario_id,
        request.form.get("contrasena", ""),
        request.form.get("confirmar_contrasena", ""),
    )
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("usuarios"))


@app.route("/api/dashboard/resumen")
@login_requerido
def api_dashboard_resumen():
    return jsonify(obtener_resumen_dashboard())


@app.route("/api/usuarios")
@admin_requerido
def api_usuarios():
    return jsonify({"usuarios": listar_usuarios(), "resumen": resumen_usuarios()})


@app.get("/api/productos")
@login_requerido
def api_productos():
    productos_registrados = listar_productos()
    return jsonify(
        {
            "productos": productos_registrados,
            "resumen": resumen_productos(productos_registrados),
        }
    )


@app.errorhandler(404)
def pagina_no_encontrada(_error):
    contexto = contexto_base("error")
    contexto.update({"page_title": "Pagina no encontrada"})
    return render_template("error404.html", **contexto), 404


def ejecutar_comando():
    if len(sys.argv) > 1 and sys.argv[1] == "init-db":
        reset = "--reset" in sys.argv
        creados = inicializar_sistema(reset=reset)
        print("Base de datos inicializada.")
        if creados:
            print("Usuarios creados:")
            for usuario, contrasena in creados:
                print(f"  {usuario} / {contrasena}")
        else:
            print("Los usuarios iniciales ya existian.")
        return True
    return False


if __name__ == "__main__":
    if not ejecutar_comando():
        inicializar_sistema(reset=False)
        app.run(debug=True, port=5000, use_reloader=False)
