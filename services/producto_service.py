from database.db import db
from models.producto import Producto


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


def crear_producto(empresa_id, datos):
    producto = Producto(
        id_empresa=empresa_id,
        nombre=datos['nombre'],
        descripcion=datos.get('descripcion'),
        sku=datos['sku'],
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
