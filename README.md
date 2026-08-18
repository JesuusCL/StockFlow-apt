# StockFlow — Sistema Web de Gestión de Inventario

Aplicación web para que PyMEs administren productos, stock y ventas de forma centralizada, con aislamiento total de datos entre empresas.

Proyecto de título — Ingeniería Informática.

## Stack tecnológico

- **Backend:** Python 3.11, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Base de datos:** MySQL 8
- **Frontend:** HTML5, Bootstrap 5, Chart.js
- **Testing:** pytest

## Instalación rápida

```bash
# 1. Clonar y entrar al proyecto
cd inventario_web

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Copiar .env.example a .env y completar tus credenciales de MySQL

# 5. Crear la base de datos (ejecutar en MySQL Workbench)
# database_scripts/01_modelo_fisico_inventario_web.sql

# 6. Verificar conexión
python test_conexion_bd.py

# 7. Levantar el servidor
python app.py
```

Accede en `http://127.0.0.1:5000`.

## Correr las pruebas

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Documentación completa

- `docs/Manual_Tecnico_StockFlow.docx` — arquitectura, modelo de datos, seguridad, conclusiones
- `docs/Manual_Usuario_StockFlow.docx` — guía de uso paso a paso
- `tests/CASOS_DE_PRUEBA.md` — casos de prueba manuales y automatizados
- `database_scripts/01_modelo_fisico_inventario_web.sql` — script SQL completo (DDL)

## Estructura del proyecto

```
inventario_web/
├── app.py                 Punto de entrada (application factory)
├── config.py               Configuración central
├── database/                Instancia compartida de SQLAlchemy
├── models/                  Entidades ORM
├── forms/                   Formularios con validaciones (WTForms)
├── routes/                  Blueprints de Flask
├── services/                 Lógica de negocio
├── templates/                Vistas Jinja2
├── static/                   CSS, JS, imágenes
├── tests/                     Suite de pruebas (pytest)
└── database_scripts/          Script SQL del modelo físico
```
