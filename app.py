import os
import sys

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from admin_dashboardAD import (
    obtener_alertas_dashboard,
    obtener_movimientos_recientes,
    obtener_resumen_dashboard,
    obtener_serie_movimientos,
)
from admin_usuariosAD import listar_usuarios, resumen_usuarios
from bd import inicializar_base_datos
from helpers import contexto_base, login_requerido
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
@login_requerido
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


@app.route("/api/dashboard/resumen")
@login_requerido
def api_dashboard_resumen():
    return jsonify(obtener_resumen_dashboard())


@app.route("/api/usuarios")
@login_requerido
def api_usuarios():
    return jsonify({"usuarios": listar_usuarios(), "resumen": resumen_usuarios()})


@app.errorhandler(404)
def pagina_no_encontrada(error):
    contexto = contexto_base("error")
    contexto.update({"page_title": "Pagina no encontrada", "error": error})
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
        puerto = int(os.environ.get("AUTOMAN_PORT", "5000"))
        app.run(debug=True, port=puerto)
