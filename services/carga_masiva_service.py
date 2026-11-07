"""
Servicio de carga masiva de productos (CSV / Excel).

Reemplaza TODO tu archivo services/carga_masiva_service.py por este,
ya incluye el soporte para la columna opcional "descripcion".
"""

import csv
import io
from decimal import Decimal, InvalidOperation
from datetime import datetime

import openpyxl

from database.db import db
from models.producto import Producto
from models.categoria import Categoria
from models.movimiento_stock import MovimientoStock
from models.carga_masiva import CargaMasiva, CargaMasivaError


def _leer_filas(archivo_storage):
    """Lee un archivo .csv o .xlsx y devuelve una lista de diccionarios
    (una fila por diccionario, claves = encabezados en minuscula)."""
    nombre_archivo = archivo_storage.filename or ""
    extension = nombre_archivo.rsplit('.', 1)[-1].lower() if '.' in nombre_archivo else ''

    filas = []

    if extension == 'csv':
        contenido = archivo_storage.read().decode('utf-8-sig')
        lector = csv.DictReader(io.StringIO(contenido))
        for fila in lector:
            fila_normalizada = {
                (k or '').strip().lower(): (v or '').strip() if v is not None else ''
                for k, v in fila.items()
            }
            if any(fila_normalizada.values()):
                filas.append(fila_normalizada)

    elif extension == 'xlsx':
        wb = openpyxl.load_workbook(archivo_storage, data_only=True)
        ws = wb.worksheets[0]
        filas_iter = ws.iter_rows(values_only=True)
        encabezados = [
            (str(h).strip().lower() if h is not None else '')
            for h in next(filas_iter)
        ]
        for fila_valores in filas_iter:
            if all(v is None or str(v).strip() == '' for v in fila_valores):
                continue
            fila_dict = {}
            for i, encabezado in enumerate(encabezados):
                if not encabezado:
                    continue
                valor = fila_valores[i] if i < len(fila_valores) else None
                fila_dict[encabezado] = '' if valor is None else str(valor).strip()
            filas.append(fila_dict)
    else:
        raise ValueError("Formato de archivo no soportado. Usa .csv o .xlsx")

    return filas


def _validar_y_crear_fila(fila, empresa_id, usuario_id):
    """Valida una fila y crea el producto (y su movimiento de stock inicial
    si corresponde). Lanza ValueError con un mensaje claro si la fila es invalida."""

    nombre = (fila.get('nombre') or '').strip()
    sku = (fila.get('sku') or '').strip()

    if not nombre:
        raise ValueError("El nombre del producto es obligatorio.")
    if not sku:
        raise ValueError("El SKU del producto es obligatorio.")

    existe = Producto.query.filter_by(id_empresa=empresa_id, sku=sku).first()
    if existe:
        raise ValueError(f"Ya existe un producto con el SKU '{sku}' en tu empresa.")

    # Categoria (opcional, se crea automaticamente si no existe)
    id_categoria = None
    nombre_categoria = (fila.get('categoria') or '').strip()
    if nombre_categoria:
        categoria = Categoria.query.filter_by(
            id_empresa=empresa_id, nombre=nombre_categoria
        ).first()
        if not categoria:
            categoria = Categoria(id_empresa=empresa_id, nombre=nombre_categoria)
            db.session.add(categoria)
            db.session.flush()
        id_categoria = categoria.id_categoria

    # Descripcion (opcional)
    descripcion = (fila.get('descripcion') or '').strip() or None

    # Precios
    try:
        precio_compra = Decimal(str(fila.get('precio_compra') or '0').replace(',', '.'))
    except InvalidOperation:
        raise ValueError(f"El precio de compra '{fila.get('precio_compra')}' no es un numero valido.")

    try:
        precio_venta = Decimal(str(fila.get('precio_venta') or '0').replace(',', '.'))
    except InvalidOperation:
        raise ValueError(f"El precio de venta '{fila.get('precio_venta')}' no es un numero valido.")

    if precio_venta < precio_compra:
        raise ValueError("El precio de venta no puede ser menor al precio de compra.")

    # Stock
    try:
        stock_inicial = int(float(fila.get('stock_inicial') or 0))
    except ValueError:
        raise ValueError(f"El stock inicial '{fila.get('stock_inicial')}' no es un numero valido.")

    try:
        stock_minimo = int(float(fila.get('stock_minimo') or 5))
    except ValueError:
        raise ValueError(f"El stock minimo '{fila.get('stock_minimo')}' no es un numero valido.")

    if stock_inicial < 0:
        raise ValueError("El stock inicial no puede ser negativo.")
    if stock_minimo < 0:
        raise ValueError("El stock minimo no puede ser negativo.")

    producto = Producto(
        id_empresa=empresa_id,
        id_categoria=id_categoria,
        nombre=nombre,
        sku=sku,
        descripcion=descripcion,
        precio_compra=precio_compra,
        precio_venta=precio_venta,
        stock_actual=stock_inicial,
        stock_minimo=stock_minimo,
        estado='activo',
    )
    db.session.add(producto)
    db.session.flush()

    if stock_inicial > 0:
        movimiento = MovimientoStock(
            id_producto=producto.id_producto,
            id_usuario=usuario_id,
            tipo_movimiento='entrada',
            cantidad=stock_inicial,
            stock_anterior=0,
            stock_posterior=stock_inicial,
            motivo='Carga masiva de productos',
        )
        db.session.add(movimiento)

    return producto


def procesar_carga(empresa_id, usuario_id, archivo_storage):
    """Procesa el archivo completo: valida fila por fila, crea los productos
    validos y registra los errores de los invalidos. Devuelve el registro
    CargaMasiva con el resumen."""

    nombre_archivo = archivo_storage.filename or "archivo_sin_nombre"
    filas = _leer_filas(archivo_storage)

    total_filas = len(filas)
    filas_exitosas = 0
    errores = []

    for i, fila in enumerate(filas, start=2):  # fila 1 = encabezado
        try:
            _validar_y_crear_fila(fila, empresa_id, usuario_id)
            db.session.commit()
            filas_exitosas += 1
        except ValueError as e:
            db.session.rollback()
            errores.append((i, str(e)))
        except Exception as e:
            db.session.rollback()
            errores.append((i, "Error inesperado al procesar la fila."))

    filas_con_error = len(errores)

    if total_filas == 0:
        estado = 'fallido'
    elif filas_con_error == 0:
        estado = 'completado'
    elif filas_exitosas == 0:
        estado = 'fallido'
    else:
        estado = 'con_errores'

    carga = CargaMasiva(
        id_empresa=empresa_id,
        id_usuario=usuario_id,
        nombre_archivo=nombre_archivo,
        total_filas=total_filas,
        filas_exitosas=filas_exitosas,
        filas_con_error=filas_con_error,
        estado=estado,
        fecha_carga=datetime.utcnow(),
    )
    db.session.add(carga)
    db.session.flush()

    for numero_fila, motivo in errores:
        db.session.add(CargaMasivaError(
            id_carga=carga.id_carga,
            numero_fila=numero_fila,
            motivo_error=motivo,
        ))

    db.session.commit()
    return carga
