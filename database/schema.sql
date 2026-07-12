CREATE TABLE IF NOT EXISTS usuarios (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(80) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(160) NOT NULL,
    correo VARCHAR(160) NOT NULL,
    documento VARCHAR(30) NOT NULL,
    rol VARCHAR(30) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
    ultimo_acceso DATETIME NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_usuarios_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tipos_producto (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(80) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_tipos_producto_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS unidades_medida (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(60) NOT NULL,
    abreviatura VARCHAR(15) NOT NULL,
    permite_decimal TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_unidades_medida_nombre (nombre),
    UNIQUE KEY uk_unidades_medida_abreviatura (abreviatura)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS categorias (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    tipo_id INT UNSIGNED NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_categorias_tipo_nombre (tipo_id, nombre),
    KEY idx_categorias_tipo (tipo_id),
    CONSTRAINT fk_categorias_tipo
        FOREIGN KEY (tipo_id) REFERENCES tipos_producto (id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS productos (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(180) NOT NULL,
    tipo_id INT UNSIGNED NOT NULL,
    categoria_id INT UNSIGNED NOT NULL,
    marca VARCHAR(100) NULL,
    descripcion TEXT NULL,
    unidad_base_id INT UNSIGNED NOT NULL,
    stock_actual DECIMAL(14,3) NOT NULL DEFAULT 0,
    stock_suelto DECIMAL(14,3) NOT NULL DEFAULT 0,
    stock_balde_abierto DECIMAL(14,3) NOT NULL DEFAULT 0,
    stock_baldes_cerrados DECIMAL(14,3) NOT NULL DEFAULT 0,
    stock_minimo DECIMAL(14,3) NOT NULL DEFAULT 0,
    observaciones TEXT NULL,
    creado_por INT UNSIGNED NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_productos_nombre (nombre),
    KEY idx_productos_tipo (tipo_id),
    KEY idx_productos_categoria (categoria_id),
    CONSTRAINT fk_productos_tipo
        FOREIGN KEY (tipo_id) REFERENCES tipos_producto (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_productos_categoria
        FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_productos_unidad
        FOREIGN KEY (unidad_base_id) REFERENCES unidades_medida (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_productos_usuario
        FOREIGN KEY (creado_por) REFERENCES usuarios (id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS presentaciones_producto (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    producto_id INT UNSIGNED NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    factor DECIMAL(14,3) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_presentaciones_producto_nombre (producto_id, nombre),
    CONSTRAINT fk_presentaciones_producto
        FOREIGN KEY (producto_id) REFERENCES productos (id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS entradas_stock (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    producto_id INT UNSIGNED NOT NULL,
    presentacion_id INT UNSIGNED NULL,
    presentacion_nombre VARCHAR(80) NOT NULL,
    factor DECIMAL(14,3) NOT NULL,
    cantidad DECIMAL(14,3) NOT NULL,
    cantidad_base DECIMAL(14,3) NOT NULL,
    origen_stock VARCHAR(30) NOT NULL DEFAULT 'suelto',
    stock_anterior DECIMAL(14,3) NOT NULL,
    stock_nuevo DECIMAL(14,3) NOT NULL,
    proveedor VARCHAR(160) NULL,
    documento VARCHAR(80) NULL,
    motivo VARCHAR(255) NOT NULL,
    usuario_id INT UNSIGNED NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_entradas_stock_producto (producto_id),
    KEY idx_entradas_stock_presentacion (presentacion_id),
    KEY idx_entradas_stock_usuario (usuario_id),
    CONSTRAINT fk_entradas_stock_producto
        FOREIGN KEY (producto_id) REFERENCES productos (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_entradas_stock_presentacion
        FOREIGN KEY (presentacion_id) REFERENCES presentaciones_producto (id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_entradas_stock_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aperturas_balde (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    producto_id INT UNSIGNED NOT NULL,
    baldes_abiertos DECIMAL(14,3) NOT NULL,
    contenido_por_balde DECIMAL(14,3) NOT NULL,
    cantidad_base DECIMAL(14,3) NOT NULL,
    stock_baldes_anterior DECIMAL(14,3) NOT NULL,
    stock_baldes_nuevo DECIMAL(14,3) NOT NULL,
    stock_abierto_anterior DECIMAL(14,3) NOT NULL,
    stock_abierto_nuevo DECIMAL(14,3) NOT NULL,
    stock_anterior DECIMAL(14,3) NOT NULL,
    stock_nuevo DECIMAL(14,3) NOT NULL,
    usuario_id INT UNSIGNED NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_aperturas_balde_producto (producto_id),
    KEY idx_aperturas_balde_usuario (usuario_id),
    CONSTRAINT fk_aperturas_balde_producto
        FOREIGN KEY (producto_id) REFERENCES productos (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_aperturas_balde_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vehiculos_atendidos (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    placa VARCHAR(20) NOT NULL,
    modelo VARCHAR(120) NULL,
    ultimo_uso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_vehiculos_atendidos_placa (placa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS salidas_stock (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    vehiculo_id INT UNSIGNED NOT NULL,
    placa VARCHAR(20) NOT NULL,
    modelo VARCHAR(120) NULL,
    trabajador VARCHAR(160) NOT NULL,
    usuario_id INT UNSIGNED NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_salidas_stock_vehiculo (vehiculo_id),
    KEY idx_salidas_stock_usuario (usuario_id),
    CONSTRAINT fk_salidas_stock_vehiculo
        FOREIGN KEY (vehiculo_id) REFERENCES vehiculos_atendidos (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_salidas_stock_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS salidas_stock_detalle (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    salida_id INT UNSIGNED NOT NULL,
    producto_id INT UNSIGNED NOT NULL,
    cantidad_base DECIMAL(14,3) NOT NULL,
    origen_stock VARCHAR(30) NOT NULL DEFAULT 'suelto',
    stock_anterior DECIMAL(14,3) NOT NULL,
    stock_nuevo DECIMAL(14,3) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_salidas_stock_detalle_salida (salida_id),
    KEY idx_salidas_stock_detalle_producto (producto_id),
    CONSTRAINT fk_salidas_stock_detalle_salida
        FOREIGN KEY (salida_id) REFERENCES salidas_stock (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_salidas_stock_detalle_producto
        FOREIGN KEY (producto_id) REFERENCES productos (id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ajustes_stock (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    producto_id INT UNSIGNED NOT NULL,
    stock_anterior DECIMAL(14,3) NOT NULL,
    stock_nuevo DECIMAL(14,3) NOT NULL,
    diferencia DECIMAL(14,3) NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    usuario_id INT UNSIGNED NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_ajustes_stock_producto (producto_id),
    KEY idx_ajustes_stock_usuario (usuario_id),
    CONSTRAINT fk_ajustes_stock_producto
        FOREIGN KEY (producto_id) REFERENCES productos (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ajustes_stock_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO tipos_producto (id, nombre) VALUES
    (1, 'Repuesto'),
    (2, 'Lubricante'),
    (3, 'Herramienta'),
    (4, 'Accesorio');

INSERT IGNORE INTO unidades_medida (id, nombre, abreviatura, permite_decimal) VALUES
    (1, 'Unidad', 'und', 0),
    (2, 'Litro', 'L', 1),
    (3, 'Galon', 'gal', 1),
    (4, 'Juego', 'jgo', 0);

INSERT IGNORE INTO categorias (id, tipo_id, nombre) VALUES
    (1, 1, 'Sin clasificar'),
    (2, 1, 'Motor'),
    (3, 1, 'Frenos'),
    (4, 1, 'Suspension'),
    (5, 1, 'Direccion'),
    (6, 1, 'Transmision'),
    (7, 1, 'Sistema electrico'),
    (8, 1, 'Filtros'),
    (9, 1, 'Refrigeracion'),
    (10, 1, 'Escape'),
    (11, 1, 'Carroceria'),
    (12, 1, 'Rodamientos y retenes'),
    (13, 2, 'Sin clasificar'),
    (14, 2, 'Aceite de motor'),
    (15, 2, 'Aceite de transmision'),
    (16, 2, 'Refrigerante'),
    (17, 2, 'Liquido de frenos'),
    (18, 3, 'Sin clasificar'),
    (19, 4, 'Sin clasificar');

CREATE TABLE IF NOT EXISTS movimientos (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    tipo VARCHAR(30) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT UNSIGNED NULL,
    PRIMARY KEY (id),
    KEY idx_movimientos_usuario (usuario_id),
    CONSTRAINT fk_movimientos_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
