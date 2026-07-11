from app import app, inicializar_sistema


if __name__ == "__main__":
    inicializar_sistema(reset=False)
    app.run(debug=False, port=5055, use_reloader=False)
