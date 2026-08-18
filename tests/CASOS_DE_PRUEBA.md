# Casos de prueba - Sistema de Inventario StockPyme

## 1. Pruebas manuales realizadas durante el desarrollo (Fases 3 a 11)

| # | Modulo | Caso | Resultado esperado | Estado |
|---|--------|------|---------------------|--------|
| 1 | Conexion BD | Conectar a MySQL con credenciales correctas | Conexion exitosa, 7 tablas visibles | OK |
| 2 | Auth | Registro con datos validos | Cuenta creada, login automatico | OK |
| 3 | Auth | Registro con correo/usuario duplicado | Rechazado con mensaje claro | OK |
| 4 | Auth | Login con credenciales correctas | Acceso concedido | OK |
| 5 | Auth | Login con contrasena incorrecta | Rechazado, mensaje generico | OK |
| 6 | Auth | Acceso a ruta privada sin sesion | Redirige a /login | OK |
| 7 | Auth | Cerrar sesion y volver atras | No permite reingresar sin loguear | OK |
| 8 | Empresa | Configurar empresa (PyME/Empresa) | Empresa asociada 1 a 1 al usuario | OK |
| 9 | Empresa | Reingresar a configuracion ya hecha | Redirige al dashboard | OK |
| 10 | Productos | Crear producto valido | Producto creado con stock en 0 | OK |
| 11 | Productos | SKU duplicado en la misma empresa | Rechazado | OK |
| 12 | Productos | Precio venta menor a precio compra | Rechazado | OK |
| 13 | Productos | Editar y eliminar producto | Cambios guardados / borrado logico | OK |
| 14 | Inventario | Entrada de stock | Stock actualizado + movimiento registrado | OK |
| 15 | Inventario | Alerta de stock bajo | Aparece cuando stock <= minimo | OK |
| 16 | Ventas | Venta con stock suficiente | Stock descontado, movimiento "salida" generado | OK |
| 17 | Ventas | Venta con stock insuficiente | Rechazada, nada se modifica | OK |
| 18 | Ventas | Filtros de historial (hoy/7 dias/mes) | Resultados correctos por rango | OK |
| 19 | Dashboard | KPIs y grafico de ventas | Datos coinciden con la BD | OK |
| 20 | Seguridad | Acceso a recurso de otra empresa por URL | 404, sin filtrar datos ajenos | OK |
| 21 | Seguridad | Pagina de error 404 personalizada | No se muestra stack trace tecnico | OK |

## 2. Pruebas automatizadas (pytest) - Fase 12

Ubicadas en `tests/`. Se ejecutan con `pytest` desde la raiz del proyecto.

| Archivo | Tipo | Cubre |
|---|---|---|
| `test_auth.py` | Unitaria + funcional | Hash de contrasena, registro, login, proteccion de rutas |
| `test_productos.py` | Funcional | CRUD, SKU duplicado, validacion de precios, **aislamiento entre empresas (IDOR)** |
| `test_ventas.py` | Integracion | Descuento de stock, calculo de total, rechazo por stock insuficiente |
| `test_inventario.py` | Integracion | Entrada de stock, generacion de movimiento, resolucion de alerta |

### Como correrlas

```
pytest
```

Para ver el detalle de cada prueba:

```
pytest -v
```

Para correr solo un archivo:

```
pytest tests/test_productos.py -v
```
