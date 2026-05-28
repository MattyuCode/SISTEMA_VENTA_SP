-- ═══════════════════════════════════════════════════════════════
--  SISTEMA SP - Soluciones Plus
--  Esquema de base de datos para PostgreSQL
-- ═══════════════════════════════════════════════════════════════

-- Crear la base de datos (ejecutar como superusuario)
-- CREATE DATABASE libreria
--     WITH ENCODING 'UTF8'
--     LC_COLLATE 'es_GT.UTF-8'
--     LC_CTYPE 'es_GT.UTF-8';

-- Conéctate a la base de datos 'libreria' antes de ejecutar lo siguiente


-- ── Tabla: categorias ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categorias (
    id      SERIAL       PRIMARY KEY,
    nombre  VARCHAR(100) UNIQUE NOT NULL
);

select * from categorias;

insert into categorias(nombre) values('Utiles Escolares');



-- ── Tabla: productos ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS productos (
    id           SERIAL       PRIMARY KEY,
    categoria_id INTEGER      REFERENCES categorias(id) ON DELETE SET NULL,
    nombre       VARCHAR(150) NOT NULL,
    tipo         VARCHAR(20)  NOT NULL DEFAULT 'Producto',  -- Producto | Servicio
    precio       REAL         NOT NULL,
    stock        INTEGER      NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_productos_nombre    ON productos(nombre);
CREATE INDEX IF NOT EXISTS idx_productos_tipo      ON productos(tipo);

select * from productos;


-- ── Tabla: ventas ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ventas (
    id     SERIAL      PRIMARY KEY,
    fecha  VARCHAR(30) NOT NULL,
    total  REAL        NOT NULL
);

select * from ventas;

CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);


-- ── Tabla: detalle_venta ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS detalle_venta (
    id          SERIAL  PRIMARY KEY,
    venta_id    INTEGER REFERENCES ventas(id)    ON DELETE CASCADE,
    producto_id INTEGER REFERENCES productos(id) ON DELETE SET NULL,
    cantidad    INTEGER NOT NULL,
    precio_unit REAL    NOT NULL,
    subtotal    REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_detalle_venta_id    ON detalle_venta(venta_id);
CREATE INDEX IF NOT EXISTS idx_detalle_producto_id ON detalle_venta(producto_id);


-- ── Tabla: observaciones (caja chica) ─────────────────────────
CREATE TABLE IF NOT EXISTS observaciones (
    id        SERIAL       PRIMARY KEY,
    fecha     VARCHAR(30)  NOT NULL,
    monto     REAL         NOT NULL,
    concepto  VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_observaciones_fecha ON observaciones(fecha);


-- ── Tabla: fiados (deudas de clientes) ────────────────────────
CREATE TABLE IF NOT EXISTS fiados (
    id          SERIAL       PRIMARY KEY,
    fecha       VARCHAR(30)  NOT NULL,
    cliente     VARCHAR(150) NOT NULL,
    total       REAL         NOT NULL DEFAULT 0,
    estado      VARCHAR(20)  NOT NULL DEFAULT 'pendiente',  -- pendiente | pagado
    fecha_pago  VARCHAR(30)  DEFAULT NULL,
    notas       VARCHAR(255) DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_fiados_estado  ON fiados(estado);
CREATE INDEX IF NOT EXISTS idx_fiados_cliente ON fiados(cliente);


-- ── Tabla: fiado_items (productos de cada fiado) ──────────────
CREATE TABLE IF NOT EXISTS fiado_items (
    id        SERIAL       PRIMARY KEY,
    fiado_id  INTEGER      NOT NULL REFERENCES fiados(id) ON DELETE CASCADE,
    producto  VARCHAR(255) NOT NULL,
    cantidad  INTEGER      NOT NULL DEFAULT 1,
    precio    REAL         NOT NULL,
    subtotal  REAL         NOT NULL
);

select * from fiado_items;

CREATE INDEX IF NOT EXISTS idx_fiado_items_fiado_id ON fiado_items(fiado_id);


--==================================================
INSERT INTO public.categorias (nombre)
VALUES
  ('Utiles Escolares'),
  ('Documentos'),
  ('Tramites'),
  ('Mantenimientos PC y Telefonos'),
  ('Reparación de Telefono y PC'),
  ('Accesorios');


--TRUNCATE TABLE public.categorias CASCADE;

select * from categorias;
