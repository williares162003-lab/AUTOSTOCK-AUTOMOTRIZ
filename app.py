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
    ajustar_stock_producto,
    crear_categoria as crear_categoria_ad,
    crear_producto as crear_producto_ad,
    crear_tipo as crear_tipo_ad,
    editar_producto as editar_producto_ad,
    editar_tipo as editar_tipo_ad,
    eliminar_categoria as eliminar_categoria_ad,
    eliminar_producto as eliminar_producto_ad,
    eliminar_tipo as eliminar_tipo_ad,
    listar_categorias,
    listar_ajustes_stock,
    listar_productos,
    listar_tipos,
    listar_unidades,
    preparar_categorias_generales,
    resumen_productos,
)
from loginAD import autenticar_usuario, preparar_usuarios_iniciales
from movimientos_entradasAD import (
    abrir_balde,
    cerrar_balde,
    listar_aperturas_balde,
    listar_entradas,
    registrar_entrada,
    resumen_entradas,
)
from movimientos_salidasAD import (
    listar_salidas,
    listar_vehiculos,
    registrar_salida,
    resumen_salidas,
)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("AUTOMAN_SECRET_KEY", "automan-dev-secret-key")


def inicializar_sistema(reset=False):
    inicializar_base_datos(reset=reset)
    preparar_categorias_generales()
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
            "page_subtitle": "Consulta que articulos hay, cuanto stock queda y que necesita reposicion.",
            "productos": productos_registrados,
            "resumen": resumen_productos(productos_registrados),
            "tipos": listar_tipos(),
            "categorias": listar_categorias(),
            "unidades": listar_unidades(),
            "ajustes": listar_ajustes_stock(),
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


@app.post("/inventario/productos/<int:producto_id>/ajustar-stock")
@login_requerido
@csrf_requerido
def ajustar_stock(producto_id):
    correcto, mensaje = ajustar_stock_producto(producto_id, request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("productos"))


@app.post("/inventario/productos/<int:producto_id>/eliminar")
@login_requerido
@csrf_requerido
def eliminar_producto(producto_id):
    correcto, mensaje = eliminar_producto_ad(producto_id)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("productos"))


@app.get("/movimientos/entradas")
@login_requerido
def entradas():
    contexto = contexto_base("entradas")
    contexto.update(
        {
            "page_title": "Entradas",
            "page_subtitle": "Registra compras y reposiciones para aumentar el stock del almacen.",
            "productos": listar_productos(),
            "entradas": listar_entradas(),
            "aperturas": listar_aperturas_balde(),
            "resumen": resumen_entradas(),
        }
    )
    return render_template("movimientos/entradas.html", **contexto)


@app.post("/movimientos/entradas/crear")
@login_requerido
@csrf_requerido
def crear_entrada():
    correcto, mensaje = registrar_entrada(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("entradas"))


@app.post("/movimientos/entradas/abrir-balde")
@login_requerido
@csrf_requerido
def abrir_balde_entrada():
    correcto, mensaje = abrir_balde(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("entradas"))


@app.post("/movimientos/entradas/cerrar-balde")
@login_requerido
@csrf_requerido
def cerrar_balde_entrada():
    correcto, mensaje = cerrar_balde(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("entradas"))


@app.get("/movimientos/salidas")
@login_requerido
def salidas():
    contexto = contexto_base("salidas")
    contexto.update(
        {
            "page_title": "Salidas",
            "page_subtitle": "Registra entregas internas por placa y trabajador.",
            "productos": listar_productos(),
            "vehiculos": listar_vehiculos(),
            "salidas": listar_salidas(),
            "resumen": resumen_salidas(),
        }
    )
    return render_template("movimientos/salidas.html", **contexto)


@app.post("/movimientos/salidas/crear")
@login_requerido
@csrf_requerido
def crear_salida():
    correcto, mensaje = registrar_salida(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("salidas"))


@app.get("/inventario/categorias")
@login_requerido
def categorias():
    tipos_registrados = listar_tipos()
    categorias_registradas = listar_categorias()
    tipo_seleccionado = request.args.get("tipo_id", type=int)
    ids_validos = {tipo["id"] for tipo in tipos_registrados}
    if tipo_seleccionado not in ids_validos:
        tipo_seleccionado = None
    categorias_visibles = [
        categoria
        for categoria in categorias_registradas
        if not tipo_seleccionado or categoria["tipo_id"] == tipo_seleccionado
    ]
    catalogo_por_nombre = {}
    for categoria in categorias_registradas:
        nombre = categoria["nombre"].strip()
        clave = nombre.lower()
        if clave == "sin clasificar":
            continue
        if clave not in catalogo_por_nombre:
            catalogo_por_nombre[clave] = {"nombre": nombre, "tipos": []}
        catalogo_por_nombre[clave]["tipos"].append(categoria["tipo_id"])
    contexto = contexto_base("categorias")
    contexto.update(
        {
            "page_title": "Tipos y categorias",
            "page_subtitle": "Organiza las familias de productos del almacen.",
            "categorias": categorias_visibles,
            "tipos": tipos_registrados,
            "tipo_seleccionado": tipo_seleccionado,
            "catalogo_categorias": sorted(
                catalogo_por_nombre.values(), key=lambda categoria: categoria["nombre"].lower()
            ),
        }
    )
    return render_template("inventario/categorias.html", **contexto)


@app.post("/inventario/tipos/crear")
@login_requerido
@csrf_requerido
def crear_tipo():
    correcto, mensaje = crear_tipo_ad(request.form)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("categorias"))


@app.post("/inventario/tipos/<int:tipo_id>/editar")
@login_requerido
@csrf_requerido
def editar_tipo(tipo_id):
    correcto, mensaje = editar_tipo_ad(tipo_id, request.form)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("categorias"))


@app.post("/inventario/tipos/<int:tipo_id>/eliminar")
@login_requerido
@csrf_requerido
def eliminar_tipo(tipo_id):
    correcto, mensaje = eliminar_tipo_ad(tipo_id)
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("categorias"))


@app.post("/inventario/categorias/crear")
@login_requerido
@csrf_requerido
def crear_categoria():
    correcto, mensaje = crear_categoria_ad(request.form)
    flash(mensaje, "success" if correcto else "error")
    tipo_id = request.form.get("tipo_id", type=int)
    return redirect(url_for("categorias", tipo_id=tipo_id) if tipo_id else url_for("categorias"))


@app.post("/inventario/categorias/<int:categoria_id>/eliminar")
@login_requerido
@csrf_requerido
def eliminar_categoria(categoria_id):
    correcto, mensaje = eliminar_categoria_ad(categoria_id)
    flash(mensaje, "success" if correcto else "error")
    tipo_id = request.form.get("tipo_id", type=int)
    return redirect(url_for("categorias", tipo_id=tipo_id) if tipo_id else url_for("categorias"))


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
