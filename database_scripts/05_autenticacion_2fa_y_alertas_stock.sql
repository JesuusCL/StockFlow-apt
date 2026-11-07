-- ============================================================
-- StockFlow - Script 05: verificacion por correo + alertas de stock
-- ============================================================
-- Crea dos tablas nuevas (no modifica ninguna tabla existente):
--   1. codigos_verificacion: codigos de 6 digitos enviados por correo al
--      iniciar sesion (se guardan con hash, nunca en texto plano).
--   2. alertas_stock_envio: guarda cuando se envio por ultima vez el correo
--      de "stock bajo" de cada empresa, para no repetirlo a cada rato.
--
-- Instrucciones: abre este archivo en MySQL Workbench, conectate a la base
-- de datos de StockFlow y ejecutalo (rayo amarillo). Debe terminar sin errores.
-- ============================================================

CREATE TABLE IF NOT EXISTS codigos_verificacion (
    id_codigo        INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario       INT NOT NULL,
    codigo_hash      VARCHAR(255) NOT NULL,
    fecha_creacion   DATETIME NOT NULL,
    fecha_expiracion DATETIME NOT NULL,
    intentos         INT NOT NULL DEFAULT 0,
    usado            TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_codigos_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
        ON DELETE CASCADE,
    INDEX idx_codigos_usuario (id_usuario, usado)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS alertas_stock_envio (
    id_empresa    INT PRIMARY KEY,
    ultimo_envio  DATETIME NOT NULL,
    CONSTRAINT fk_alertas_empresa
        FOREIGN KEY (id_empresa) REFERENCES empresas (id_empresa)
        ON DELETE CASCADE
) ENGINE=InnoDB;
