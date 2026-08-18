-- ============================================================
-- SISTEMA WEB DE GESTION DE INVENTARIO - StockPyme
-- Script: Modelo fisico (DDL)
-- Servidor destino: Inventario_web (127.0.0.1:3306)
-- Fase 2 - Base de datos
-- ============================================================

USE Inventario_web;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- Tabla: usuarios
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario  VARCHAR(50)  NOT NULL,
    correo          VARCHAR(120) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    fecha_registro  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_usuarios_username UNIQUE (nombre_usuario),
    CONSTRAINT uq_usuarios_correo   UNIQUE (correo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: empresas
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS empresas (
    id_empresa      INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT NOT NULL,
    nombre_empresa  VARCHAR(150) NOT NULL,
    tipo_negocio    ENUM('pyme', 'empresa') NOT NULL,
    rut             VARCHAR(20)  NULL,
    telefono        VARCHAR(20)  NULL,
    direccion       VARCHAR(255) NULL,
    fecha_creacion  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_empresas_usuario UNIQUE (id_usuario),
    CONSTRAINT fk_empresas_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: categorias
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    id_empresa   INT NOT NULL,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255) NULL,
    CONSTRAINT uq_categoria_empresa_nombre UNIQUE (id_empresa, nombre),
    CONSTRAINT fk_categorias_empresa FOREIGN KEY (id_empresa)
        REFERENCES empresas(id_empresa) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: productos
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id_producto     INT AUTO_INCREMENT PRIMARY KEY,
    id_empresa      INT NOT NULL,
    id_categoria    INT NULL,
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT NULL,
    sku             VARCHAR(50)  NOT NULL,
    precio_compra   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    precio_venta    DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock_actual    INT NOT NULL DEFAULT 0,
    stock_minimo    INT NOT NULL DEFAULT 5,
    estado          ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_producto_empresa_sku UNIQUE (id_empresa, sku),
    CONSTRAINT fk_productos_empresa FOREIGN KEY (id_empresa)
        REFERENCES empresas(id_empresa) ON DELETE CASCADE,
    CONSTRAINT fk_productos_categoria FOREIGN KEY (id_categoria)
        REFERENCES categorias(id_categoria) ON DELETE SET NULL,
    CONSTRAINT chk_stock_no_negativo CHECK (stock_actual >= 0),
    CONSTRAINT chk_precios_no_negativos CHECK (precio_compra >= 0 AND precio_venta >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_productos_empresa ON productos(id_empresa);
CREATE INDEX idx_productos_nombre  ON productos(nombre);

-- ------------------------------------------------------------
-- Tabla: movimientos_stock
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movimientos_stock (
    id_movimiento   INT AUTO_INCREMENT PRIMARY KEY,
    id_producto     INT NOT NULL,
    id_usuario      INT NOT NULL,
    tipo_movimiento ENUM('entrada', 'salida') NOT NULL,
    cantidad        INT NOT NULL,
    stock_anterior  INT NOT NULL,
    stock_posterior INT NOT NULL,
    motivo          VARCHAR(255) NULL,
    fecha           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movimientos_producto FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto) ON DELETE CASCADE,
    CONSTRAINT fk_movimientos_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_movimientos_producto ON movimientos_stock(id_producto);
CREATE INDEX idx_movimientos_fecha    ON movimientos_stock(fecha);

-- ------------------------------------------------------------
-- Tabla: ventas
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ventas (
    id_venta   INT AUTO_INCREMENT PRIMARY KEY,
    id_empresa INT NOT NULL,
    id_usuario INT NOT NULL,
    fecha      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    estado     ENUM('completada', 'anulada') NOT NULL DEFAULT 'completada',
    CONSTRAINT fk_ventas_empresa FOREIGN KEY (id_empresa)
        REFERENCES empresas(id_empresa) ON DELETE CASCADE,
    CONSTRAINT fk_ventas_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT chk_total_no_negativo CHECK (total >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_ventas_empresa ON ventas(id_empresa);
CREATE INDEX idx_ventas_fecha   ON ventas(fecha);

-- ------------------------------------------------------------
-- Tabla: detalle_ventas
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id_detalle      INT AUTO_INCREMENT PRIMARY KEY,
    id_venta        INT NOT NULL,
    id_producto     INT NOT NULL,
    cantidad        INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal        DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_detalle_venta FOREIGN KEY (id_venta)
        REFERENCES ventas(id_venta) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto) ON DELETE RESTRICT,
    CONSTRAINT chk_cantidad_detalle_positiva CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_detalle_venta    ON detalle_ventas(id_venta);
CREATE INDEX idx_detalle_producto ON detalle_ventas(id_producto);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- Notas de diseno:
-- - Borrado logico en productos/ventas via columna "estado".
-- - ON DELETE RESTRICT en usuario->movimientos/ventas: no se
--   permite borrar un usuario si tiene historial asociado,
--   protegiendo la trazabilidad.
-- - ON DELETE CASCADE en empresa->productos/categorias/ventas:
--   si se elimina una empresa (caso administrativo), se limpia
--   toda su informacion asociada.
-- - CHECK constraints requieren MySQL 8.0.16+ para ser exigidos
--   realmente (versiones anteriores los aceptan pero los ignoran).
-- ============================================================
