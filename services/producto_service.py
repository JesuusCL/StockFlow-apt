import os
import uuid

from flask import current_app

from database.db import db
from models.producto import Producto

EXTENSIONES_PERMITIDAS = {'jpg', 'jpeg', 'png', 'webp'}
CARPETA_UPLOADS_RELATIVA = os.path.join('uploads', 'productos')


def listar_productos(empresa_id, busqueda=None, categoria_id=None, orden='nombre'):
    """
    Devuelve productos activos de la empresa, con busqueda opcional por
    nombre/SKU, filtro opcional por categoria, y orden configurable.
    """
    query = Producto.query.filter_by(id_empresa=empresa_id, estado='activo')

    if busqueda:
        patron = f'%{busqueda}%'
        query = query.filter(
            db.or_(Producto.nombre.ilike(patron), Producto.sku.ilike(patron))
        )

    if categoria_id:
        query = query.filter_by(id_categoria=categoria_id)

    columnas_orden = {
        'nombre': Producto.nombre,
        'stock': Producto.stock_actual,
        'precio': Producto.precio_venta,
    }
    query = query.order_by(columnas_orden.get(orden, Producto.nombre))

    return query


def obtener_producto_de_empresa(producto_id, empresa_id):
    """
    Devuelve el producto solo si pertenece a la empresa indicada.
    Esta es la funcion clave que garantiza el aislamiento entre empresas:
    nunca se busca un producto solo por su id_producto.
    """
    return Producto.query.filter_by(id_producto=producto_id, id_empresa=empresa_id).first()


def _extension_valida(nombre_archivo):
    return '.' in nombre_archivo and nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS


def guardar_imagen_producto(archivo_storage):
    """
    Guarda la foto subida en static/uploads/productos/ con un nombre unico
    (para que nunca choquen dos productos con la misma foto) y devuelve el
    nombre de archivo generado, listo para guardar en la base de datos.

    Devuelve None si no se subio ningun archivo nuevo. Al editar un producto,
    el formulario trae como "dato" el nombre de la foto actual (un texto, no un
    archivo): getattr(..., 'filename', None) lo trata como "sin archivo nuevo".
    """
    nombre_original = getattr(archivo_storage, 'filename', None)
    if not nombre_original:
        return None

    if not _extension_valida(nombre_original):
        return None

    extension = nombre_original.rsplit('.', 1)[1].lower()
    nombre_unico = f"{uuid.uuid4().hex}.{extension}"

    carpeta_destino = os.path.join(current_app.root_path, 'static', CARPETA_UPLOADS_RELATIVA)
    os.makedirs(carpeta_destino, exist_ok=True)

    archivo_storage.save(os.path.join(carpeta_destino, nombre_unico))

    return nombre_unico


def eliminar_imagen_producto(nombre_archivo):
    """Borra del disco la foto anterior de un producto, si existe."""
    if not nombre_archivo:
        return

    ruta = os.path.join(current_app.root_path, 'static', CARPETA_UPLOADS_RELATIVA, nombre_archivo)
    if os.path.exists(ruta):
        os.remove(ruta)


def crear_producto(empresa_id, datos):
    producto = Producto(
        id_empresa=empresa_id,
        nombre=datos['nombre'],
        descripcion=datos.get('descripcion'),
        sku=datos['sku'],
        imagen=datos.get('imagen'),
        id_categoria=datos.get('id_categoria') or None,
        precio_compra=datos['precio_compra'],
        precio_venta=datos['precio_venta'],
        stock_minimo=datos['stock_minimo'],
        stock_actual=0,
    )
    db.session.add(producto)
    db.session.commit()
    return producto


def actualizar_producto(producto, datos):
    producto.nombre = datos['nombre']
    producto.descripcion = datos.get('descripcion')
    producto.sku = datos['sku']
    producto.id_categoria = datos.get('id_categoria') or None
    producto.precio_compra = datos['precio_compra']
    producto.precio_venta = datos['precio_venta']
    producto.stock_minimo = datos['stock_minimo']

    # La imagen solo se reemplaza si se subio una nueva; si no, se mantiene
    # la que el producto ya tenia.
    nueva_imagen = datos.get('imagen')
    if nueva_imagen:
        eliminar_imagen_producto(producto.imagen)
        producto.imagen = nueva_imagen

    db.session.commit()
    return producto


def eliminar_producto(producto):
    """Borrado logico: nunca se elimina fisicamente, para no romper historial
    de ventas ni movimientos de stock asociados (regla del punto 21)."""
    producto.estado = 'inactivo'
    db.session.commit()


def productos_con_stock_bajo(empresa_id):
    return (Producto.query
            .filter_by(id_empresa=empresa_id, estado='activo')
            .filter(Producto.stock_actual <= Producto.stock_minimo)
            .order_by(Producto.stock_actual)
            .all())
