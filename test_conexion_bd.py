"""
Script de diagnostico de conexion a la base de datos.
Ejecutar con: python test_conexion_bd.py
No requiere que Flask este corriendo.
"""
from sqlalchemy import create_engine, text
from config import Config

print(f"Intentando conectar a: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")

try:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        resultado = conn.execute(text("SHOW TABLES;"))
        tablas = [fila[0] for fila in resultado]

        print("Conexion exitosa.")
        print(f"Tablas encontradas ({len(tablas)}):")
        for tabla in tablas:
            print(f"  - {tabla}")

        if len(tablas) == 0:
            print("\nAviso: no se encontraron tablas. Verifica que ejecutaste "
                  "01_modelo_fisico_inventario_web.sql en este schema.")

except Exception as error:
    print("Error al conectar con la base de datos.")
    print(f"Detalle: {error}")
