# Evidencias individuales · StockFlow

Evidencias de pruebas, arquitectura y base de datos del sistema StockFlow.
Las pruebas se ejecutaron el 20-11-2026 sobre la versión del repositorio en la rama `main`.

**Contenido**

1. [Resultados de ejecución de pytest](#1-resultados-de-ejecución-de-pytest)
2. [Casos de prueba automatizados](#2-casos-de-prueba-automatizados)
3. [Casos de prueba manuales](#3-casos-de-prueba-manuales)
4. [Arquitectura en capas](#4-arquitectura-en-capas)
5. [Modelo relacional y esquema físico](#5-modelo-relacional-y-esquema-físico)
6. [Archivos de respaldo](#6-archivos-de-respaldo)

---

## 1. Resultados de ejecución de pytest

Ejecución de la suite completa desde el panel *Testing* de VS Code: **36 de 36 pruebas aprobadas**.

![Resultados de pytest en VS Code, parte 1](01_pytest_vscode_resultados_parte1.png)

![Resultados de pytest en VS Code, parte 2](02_pytest_vscode_resultados_parte2.png)

## 2. Casos de prueba automatizados

Los 36 casos de `tests/`, con su resultado esperado y el resultado real de la ejecución.

![Casos de prueba automatizados, parte 1: 2FA y alertas de stock](03_casos_automatizados_parte1.png)

![Casos de prueba automatizados, parte 2: autenticación, inventario, productos y ventas](03_casos_automatizados_parte2.png)

## 3. Casos de prueba manuales

Los 21 casos de `tests/CASOS_DE_PRUEBA.md`, ejecutados en la aplicación con el resultado real obtenido.

![Casos de prueba manuales, parte 1](04_casos_manuales_parte1.png)

![Casos de prueba manuales, parte 2](04_casos_manuales_parte2.png)

Caso 1: conexión exitosa a la base de datos `inventario_web` (11 tablas).

![Caso 1: conexión a la base de datos](05_caso1_conexion_bd.png)

## 4. Arquitectura en capas

Comunicación entre el navegador, Flask, la capa de presentación, el middleware de seguridad, los blueprints, los servicios, los modelos SQLAlchemy y MySQL.

![Arquitectura en capas de StockFlow](06_arquitectura_en_capas.png)

## 5. Modelo relacional y esquema físico

Diagrama EER generado con MySQL Workbench por ingeniería inversa de la base `inventario_web`.

![Modelo relacional generado desde MySQL Workbench](07_modelo_relacional_workbench.png)

Modelo relacional con claves primarias, claves foráneas, cardinalidades y reglas `ON DELETE`.

![Modelo relacional con PK, FK y relaciones](07_modelo_relacional.png)

Esquema físico: claves primarias, claves foráneas, restricciones `UNIQUE`, `CHECK` e índices de cada tabla.

![Esquema físico: claves y restricciones](08_esquema_fisico_restricciones.png)

## 6. Archivos de respaldo

| Archivo | Contenido |
|---|---|
| [`resultado_pytest.txt`](resultado_pytest.txt) | Salida de texto de `pytest -v` |
| [`resultado_pytest.xml`](resultado_pytest.xml) | Resultado en formato JUnit XML |
| [`resultado_pytest_con_avisos.txt`](resultado_pytest_con_avisos.txt) | Salida completa, incluidas las advertencias |
| [`modelo_inventario_web.mwb`](modelo_inventario_web.mwb) | Modelo de MySQL Workbench (se abre con Workbench 8.0) |

Otra evidencia de la carpeta:

![Evidencia adicional](Evidencia-img1.png)
