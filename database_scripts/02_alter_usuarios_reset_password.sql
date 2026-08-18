-- ============================================================
-- Alteracion: soporte para recuperacion de contrasena
-- Ejecutar en el schema inventario_web_db
-- ============================================================

USE inventario_web_db;

ALTER TABLE usuarios
    ADD COLUMN reset_token VARCHAR(100) NULL,
    ADD COLUMN reset_token_expira DATETIME NULL;
