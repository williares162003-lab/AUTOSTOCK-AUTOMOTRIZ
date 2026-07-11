# Base de datos

El sistema usa MySQL/MariaDB: XAMPP en desarrollo y MySQL en PythonAnywhere.

- `schema.sql`: estructura de tablas.
- `schema.sql`: crea las tablas del sistema en la base indicada por `DB_NAME`.

Inicializacion:

```bash
python app.py init-db
```

Reiniciar desde cero:

```bash
python app.py init-db --reset
```
