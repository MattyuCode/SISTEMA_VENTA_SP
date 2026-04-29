use libreria;

-- ALTER USER 'root'@'localhost' identified BY 'adminsp';
-- CREATE DATABASE libreria CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- insert into libreria.categorias(nombre) values ('Documentos');

ALTER TABLE libreria.productos ADD COLUMN tipo VARCHAR(20) NOT NULL DEFAULT 'Producto';


-- Primero verifica si la columna ya existe
ALTER TABLE libreria.productos ADD COLUMN tipo VARCHAR(20) NOT NULL DEFAULT 'Producto';

-- Actualiza los registros existentes
UPDATE libreria.productos SET tipo = 'Producto' WHERE tipo = '' OR tipo IS NULL;

 SELECT id, nombre, variante, tipo FROM productos;


CREATE TABLE IF NOT EXISTS observaciones (
    id       INT PRIMARY KEY AUTO_INCREMENT,
    fecha    VARCHAR(30) NOT NULL,
    monto    FLOAT NOT NULL,
    concepto VARCHAR(255) NOT NULL
);


select * from observaciones;

 
-- Nueva estructura: deuda maestra + items
CREATE TABLE IF NOT EXISTS fiados (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    fecha       VARCHAR(30) NOT NULL,
    cliente     VARCHAR(150) NOT NULL,
    total       FLOAT NOT NULL DEFAULT 0,
    estado      VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    fecha_pago  VARCHAR(30) DEFAULT NULL,
    notas       VARCHAR(255) DEFAULT ''
);

CREATE TABLE IF NOT EXISTS fiado_items (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    fiado_id   INT NOT NULL,
    producto   VARCHAR(255) NOT NULL,
    cantidad   INT NOT NULL DEFAULT 1,
    precio     FLOAT NOT NULL,
    subtotal   FLOAT NOT NULL,
    FOREIGN KEY (fiado_id) REFERENCES fiados(id) ON DELETE CASCADE
);

SELECT * FROM FIADOS;











