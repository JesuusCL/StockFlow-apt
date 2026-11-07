-- ============================================================
-- StockFlow - Carga masiva de productos (CSV/Excel)
-- Ejecutar en el schema inventario_web_db
-- ============================================================

USE inventario_web_db;

CREATE TABLE IF NOT EXISTS cargas_masivas (
    id_carga        INT AUTO_INCREMENT PRIMARY KEY,
    id_empresa      INT NOT NULL,
    id_usuario      INT NOT NULL,
    nombre_archivo  VARCHAR(255) NOT NULL,
    total_filas     INT NOT NULL DEFAULT 0,
    filas_exitosas  INT NOT NULL DEFAULT 0,
    filas_con_error INT NOT NULL DEFAULT 0,
    estado          ENUM('completado', 'con_errores', 'fallido') NOT NULL DEFAULT 'completado',
    fecha_carga     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_carga_empresa FOREIGN KEY (id_empresa)
        REFERENCES empresas(id_empresa) ON DELETE CASCADE,
    CONSTRAINT fk_carga_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cargas_masivas_errores (
    id_error     INT AUTO_INCREMENT PRIMARY KEY,
    id_carga     INT NOT NULL,
    numero_fila  INT NOT NULL,
    motivo_error VARCHAR(255) NOT NULL,
    CONSTRAINT fk_error_carga FOREIGN KEY (id_carga)
        REFERENCES cargas_masivas(id_carga) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_carga_empresa ON cargas_masivas(id_empresa);
