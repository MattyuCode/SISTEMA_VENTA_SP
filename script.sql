-- ═══════════════════════════════════════════════════════════════
--  SISTEMA SP - Soluciones Plus
--  Esquema de base de datos para MYSQL
-- ═══════════════════════════════════════════════════════════════

-- ALTER USER 'root'@'localhost' identified BY 'adminsp';

-- ================== Crear la base de datos (ejecutar como superusuario)
-- CREATE DATABASE libreria CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- use libreria;

-- insert into libreria.categorias(nombre) values ('Documentos');

SET FOREIGN_KEY_CHECKS = 0; 
TRUNCATE TABLE detalle_venta; 
SET FOREIGN_KEY_CHECKS = 1;



CREATE TABLE IF NOT EXISTS categorias (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productos (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id INT,
    nombre       VARCHAR(150) NOT NULL,
    tipo         VARCHAR(20)  NOT NULL DEFAULT 'Producto',
    precio       DECIMAL(10,2) NOT NULL,
    stock        INT NOT NULL DEFAULT 0,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    INDEX idx_productos_categoria (categoria_id),
    INDEX idx_productos_nombre (nombre),
    INDEX idx_productos_tipo (tipo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ventas (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    INDEX idx_ventas_fecha (fecha)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS detalle_venta (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    venta_id    INT,
    producto_id INT,
    cantidad    INT NOT NULL,
    precio_unit DECIMAL(10,2) NOT NULL,
    subtotal    DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE SET NULL,
    INDEX idx_detalle_venta_id (venta_id),
    INDEX idx_detalle_producto_id (producto_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS observaciones (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    fecha    DATETIME NOT NULL,
    monto    DECIMAL(10,2) NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    INDEX idx_observaciones_fecha (fecha)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fiados (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    fecha      DATETIME NOT NULL,
    cliente    VARCHAR(150) NOT NULL,
    total      DECIMAL(10,2) NOT NULL DEFAULT 0,
    estado     VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    fecha_pago DATETIME DEFAULT NULL,
    notas      VARCHAR(255) DEFAULT '',
    INDEX idx_fiados_estado (estado),
    INDEX idx_fiados_cliente (cliente)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fiado_items (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    fiado_id INT NOT NULL,
    producto VARCHAR(255) NOT NULL,
    cantidad INT NOT NULL DEFAULT 1,
    precio   DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (fiado_id) REFERENCES fiados(id) ON DELETE CASCADE,
    INDEX idx_fiado_items_fiado_id (fiado_id)
) ENGINE=InnoDB;










