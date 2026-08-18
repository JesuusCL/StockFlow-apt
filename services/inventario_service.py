from database.db import db
from models.producto import Producto
from models.movimiento_stock import MovimientoStock


def registrar_entrada(producto, cantidad, usuario_id, motivo=None):
    """
    Aumenta el stock del producto y deja registro del movimiento.
    Ambas operaciones se confirman juntas (misma sesion de SQLAlchemy):
    si algo falla, no queda el stock actualizado sin su movimiento asociado.
    """
    stock_anterior = producto.stock_actual
    producto.stock_actual = stock_anterior + cantidad

    movimiento = MovimientoStock(
        id_producto=producto.id_producto,
        id_usuario=usuario_id,
        tipo_movimiento='entrada',
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_posterior=producto.stock_actual,
        motivo=motivo,
    )
    db.session.add(movimiento)
    db.session.commit()
    return movimiento


def listar_movimientos(empresa_id, producto_id=None):
    """Historial de movimientos, acotado siempre a productos de la empresa del usuario."""
    query = (MovimientoStock.query
             .join(Producto, MovimientoStock.id_producto == Producto.id_producto)
             .filter(Producto.id_empresa == empresa_id))

    if producto_id:
        query = query.filter(MovimientoStock.id_producto == producto_id)

    return query.order_by(MovimientoStock.fecha.desc())
