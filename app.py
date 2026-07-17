import os
import sys

from flask import Flask, Response, flash, jsonify, redirect, render_template, request, session, url_for

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
from bd import inicializar_base_datos, limpiar_almacen
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
    listar_areas,
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
    abrir_caja,
    abrir_cilindro,
    cerrar_balde,
    cerrar_cilindro,
    listar_aperturas_balde,
    listar_entradas,
    registrar_entrada,
    resumen_entradas,
)
from movimientos_kardexAD import (
    listar_movimientos_kardex_con_errores,
    obtener_producto_kardex,
    resumen_kardex,
)
from movimientos_salidasAD import (
    anular_salida as anular_salida_ad,
    corregir_detalle_salida as corregir_detalle_salida_ad,
    listar_salidas,
    listar_vehiculos,
    registrar_salida,
    renombrar_destino,
    resumen_salidas,
)
from reportesAD import generar_reporte_csv, obtener_reporte_general


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("AUTOMAN_SECRET_KEY", "automan-dev-secret-key")


def tipos_desde_productos(productos):
    tipos = {}
    for producto in productos:
        tipo_id = producto.get("tipo_id")
        tipo = producto.get("tipo")
        area_id = producto.get("area_id")
        area = producto.get("area")
        if tipo_id and tipo and tipo_id not in tipos:
            tipos[tipo_id] = {"id": tipo_id, "nombre": tipo, "area_id": area_id, "area": area}
    return sorted(tipos.values(), key=lambda item: (item.get("area_id") or 0, item["nombre"]))


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
            "areas": listar_areas(),
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
    productos_registrados = listar_productos()
    contexto = contexto_base("entradas")
    contexto.update(
        {
            "page_title": "Entradas",
            "page_subtitle": "Registra compras y reposiciones para aumentar el stock del almacen.",
            "areas": listar_areas(),
            "tipos": tipos_desde_productos(productos_registrados),
            "categorias": listar_categorias(),
            "productos": productos_registrados,
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


@app.post("/movimientos/entradas/abrir-caja")
@login_requerido
@csrf_requerido
def abrir_caja_entrada():
    correcto, mensaje = abrir_caja(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("entradas"))


@app.post("/movimientos/entradas/cerrar-balde")
@login_requerido
@csrf_requerido
def cerrar_balde_entrada():
    correcto, mensaje = cerrar_balde(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("entradas"))


@app.post("/movimientos/entradas/abrir-cilindro")
@login_requerido
@csrf_requerido
def abrir_cilindro_entrada():
    correcto, mensaje = abrir_cilindro(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("entradas"))


@app.post("/movimientos/entradas/cerrar-cilindro")
@login_requerido
@csrf_requerido
def cerrar_cilindro_entrada():
    correcto, mensaje = cerrar_cilindro(request.form, session["usuario"]["id"])
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("entradas"))


@app.get("/movimientos/salidas")
@login_requerido
def salidas():
    productos_registrados = listar_productos()
    contexto = contexto_base("salidas")
    contexto.update(
        {
            "page_title": "Salidas",
            "page_subtitle": "Registra entregas internas por placa y trabajador.",
            "areas": listar_areas(),
            "tipos": tipos_desde_productos(productos_registrados),
            "categorias": listar_categorias(),
            "productos": productos_registrados,
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


@app.post("/movimientos/salidas/<int:salida_id>/anular")
@login_requerido
@csrf_requerido
def anular_salida(salida_id):
    correcto, mensaje = anular_salida_ad(
        salida_id,
        request.form.get("motivo", ""),
        session["usuario"]["id"],
    )
    flash(mensaje, "success" if correcto else "error")
    return redirect(url_for("salidas"))


@app.post("/movimientos/salidas/detalle/<int:detalle_id>/corregir")
@login_requerido
@csrf_requerido
def corregir_detalle_salida(detalle_id):
    correcto, mensaje = corregir_detalle_salida_ad(
        detalle_id,
        request.form,
        session["usuario"]["id"],
    )
    flash(mensaje, "success" if correcto else "error")
    return_to = request.form.get("return_to", "")
    if not return_to.startswith("/") or return_to.startswith("//"):
        return_to = url_for("salidas")
    return redirect(return_to)


@app.get("/movimientos/kardex")
@login_requerido
def kardex():
    filtros = {
        "producto_id": request.args.get("producto_id", ""),
        "area_id": request.args.get("area_id", ""),
        "tipo_id": request.args.get("tipo_id", ""),
        "categoria_id": request.args.get("categoria_id", ""),
        "fecha_inicio": request.args.get("fecha_inicio", ""),
        "fecha_fin": request.args.get("fecha_fin", ""),
        "tipo": request.args.get("tipo", ""),
        "placa": request.args.get("placa", "").strip().upper(),
    }
    errores_kardex = []
    try:
        movimientos, errores_kardex = listar_movimientos_kardex_con_errores(filtros)
    except Exception:
        app.logger.exception("No se pudo cargar el kardex")
        movimientos = []
        errores_kardex.append(
            {
                "mensaje": "No se pudo cargar el historial.",
                "detalle": "Actualiza la base de datos con python app.py init-db.",
            }
        )
    producto_id = request.args.get("producto_id", type=int)
    producto_seleccionado = None
    if producto_id:
        try:
            producto_seleccionado = obtener_producto_kardex(producto_id)
        except Exception:
            app.logger.exception("No se pudo cargar el producto del kardex")
            errores_kardex.append(
                {
                    "mensaje": "No se pudo cargar el resumen del producto seleccionado.",
                    "detalle": "Revisa que la tabla productos tenga las columnas nuevas de stock.",
                }
            )
    contexto = contexto_base("kardex")
    contexto.update(
        {
            "page_title": "Kardex",
            "page_subtitle": "Consulta el historial de entradas, salidas, ajustes y control de envases.",
            "areas": listar_areas(),
            "tipos": listar_tipos(),
            "categorias": listar_categorias(),
            "productos": listar_productos(),
            "producto_seleccionado": producto_seleccionado,
            "movimientos": movimientos,
            "resumen": resumen_kardex(movimientos),
            "filtros": filtros,
            "errores_kardex": errores_kardex,
        }
    )
    return render_template("movimientos/kardex.html", **contexto)


@app.get("/inventario/categorias")
@login_requerido
def categorias():
    areas_registradas = listar_areas()
    tipos_registrados = listar_tipos()
    categorias_registradas = listar_categorias()
    area_seleccionada = request.args.get("area_id", type=int)
    tipo_seleccionado = request.args.get("tipo_id", type=int)
    areas_validas = {area["id"] for area in areas_registradas}
    if area_seleccionada not in areas_validas:
        area_seleccionada = None
    tipos_visibles = [
        tipo
        for tipo in tipos_registrados
        if not area_seleccionada or tipo["area_id"] == area_seleccionada
    ]
    ids_validos = {tipo["id"] for tipo in tipos_visibles}
    if tipo_seleccionado not in ids_validos:
        tipo_seleccionado = None
    categorias_visibles = [
        categoria
        for categoria in categorias_registradas
        if (not area_seleccionada or categoria["area_id"] == area_seleccionada)
        and (not tipo_seleccionado or categoria["tipo_id"] == tipo_seleccionado)
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
            "areas": areas_registradas,
            "categorias": categorias_visibles,
            "tipos": tipos_visibles,
            "todos_tipos": tipos_registrados,
            "area_seleccionada": area_seleccionada,
            "tipo_seleccionado": tipo_seleccionado,
            "catalogo_categorias": sorted(
                catalogo_por_nombre.values(), key=lambda categoria: categoria["nombre"].lower()
            ),
        }
    )
    return render_template("inventario/categorias.html", **contexto)


@app.get("/reportes")
@login_requerido
def reportes():
    reporte = obtener_reporte_general(
        {
            "fecha_inicio": request.args.get("fecha_inicio", ""),
            "fecha_fin": request.args.get("fecha_fin", ""),
            "placa": request.args.get("placa", ""),
        }
    )
    contexto = contexto_base("reportes")
    contexto.update(
        {
            "page_title": "Reportes",
            "page_subtitle": "Analiza stock, entradas, salidas y actividad del almacen.",
            **reporte,
        }
    )
    return render_template("reportes/general.html", **contexto)


@app.get("/reportes/exportar")
@login_requerido
def exportar_reportes():
    nombre_archivo, contenido = generar_reporte_csv(
        {
            "fecha_inicio": request.args.get("fecha_inicio", ""),
            "fecha_fin": request.args.get("fecha_fin", ""),
            "placa": request.args.get("placa", ""),
        }
    )
    respuesta = Response("\ufeff" + contenido, mimetype="text/csv; charset=utf-8")
    respuesta.headers["Content-Disposition"] = f"attachment; filename={nombre_archivo}"
    return respuesta


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
    area_id = request.form.get("area_id", type=int)
    tipo_id = request.form.get("tipo_id", type=int)
    if tipo_id:
        return redirect(url_for("categorias", area_id=area_id, tipo_id=tipo_id))
    return redirect(url_for("categorias", area_id=area_id) if area_id else url_for("categorias"))


@app.post("/inventario/categorias/<int:categoria_id>/eliminar")
@login_requerido
@csrf_requerido
def eliminar_categoria(categoria_id):
    correcto, mensaje = eliminar_categoria_ad(categoria_id)
    flash(mensaje, "success" if correcto else "error")
    area_id = request.form.get("area_id", type=int)
    tipo_id = request.form.get("tipo_id", type=int)
    if tipo_id:
        return redirect(url_for("categorias", area_id=area_id, tipo_id=tipo_id))
    return redirect(url_for("categorias", area_id=area_id) if area_id else url_for("categorias"))


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
    if len(sys.argv) > 1 and sys.argv[1] == "check-kardex":
        movimientos, errores = listar_movimientos_kardex_con_errores({})
        print(f"Kardex: {len(movimientos)} movimientos leidos.")
        if errores:
            print("Errores encontrados:")
            for error in errores:
                print(f"  - {error['mensaje']} {error['detalle']}")
        else:
            print("Kardex sin errores.")
        return True
    if len(sys.argv) > 1 and sys.argv[1] == "limpiar-almacen":
        if "--confirmar" not in sys.argv:
            print("Este comando borra productos, categorias, movimientos, entradas y salidas.")
            print("Conserva usuarios y unidades de medida.")
            print("Para ejecutarlo usa: python app.py limpiar-almacen --confirmar")
            return True
        inicializar_base_datos(reset=False)
        limpiar_almacen()
        preparar_usuarios_iniciales()
        print("Almacen limpio. Usuarios y unidades de medida conservados.")
        return True
    if len(sys.argv) > 1 and sys.argv[1] == "renombrar-destino":
        if len(sys.argv) != 4:
            print('Uso: python app.py renombrar-destino "DESTINO ANTERIOR" "DESTINO NUEVO"')
            return True
        inicializar_base_datos(reset=False)
        correcto, mensaje, resultado = renombrar_destino(sys.argv[2], sys.argv[3])
        print(mensaje)
        if correcto:
            print(f"Salidas actualizadas: {resultado.get('salidas', 0)}")
            print(f"Destinos actualizados: {resultado.get('destinos', 0)}")
        return True
    return False


if __name__ == "__main__":
    if not ejecutar_comando():
        inicializar_sistema(reset=False)
        app.run(debug=True, port=5000, use_reloader=False)
