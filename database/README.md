# Base de datos

El sistema usa SQLite para desarrollo y despliegue inicial en PythonAnywhere.

- `schema.sql`: estructura de tablas.
- `automan.sqlite3`: base local generada, no se sube a GitHub.

Inicializacion:

```bash
python app.py init-db
```

Reiniciar desde cero:

```bash
python app.py init-db --reset
```
