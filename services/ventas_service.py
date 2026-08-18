from decimal import Decimal
from datetime import datetime, timedelta

from database.db import db
from models.producto import Producto
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.movimiento_stock import MovimientoStock


def registrar_venta(empresa_id, usuario_id, items):
    """
    items: lista de dicts {'producto_id': int, 'cantidad': int}

    Valida TODAS las lineas antes de escribir cualquier cosa en la base de
    datos. Si una sola linea es invalida (producto de otra empresa, stock
    insuficiente, cantidad invalida), no se crea la venta.
    """
    if not items:
        raise ValueError('La venta debe contener al menos un producto.')

    lineas_validadas = []
    total = Decimal('0.00')

    for item in items:
        producto = Producto.query.filter_by(
            id_producto=item['producto_id'], id_empresa=empresa_id, estado='activo'
        ).first()

        if producto is None:
            raise ValueError('Uno de los productos seleccionados no es valido.')

        cantidad = item['cantidad']
        if cantidad <= 0:
            raise ValueError(f'La cantidad para "{producto.nombre}" debe ser mayor a 0.')

        if cantidad > producto.stock_actual:
            raise ValueError(
                f'Stock insuficiente para "{producto.nombre}". '
                f'Disponible: {producto.stock_actual}, solicitado: {cantidad}.'
            )

        subtotal = producto.precio_venta * cantidad
        total += subtotal
        lineas_validadas.append((producto, cantidad, subtotal))

    # A partir de aqui, todas las lineas son validas: se escribe en la base de datos
    venta = Venta(id_empresa=empresa_id, id_usuario=usuario_id, total=total)
    db.session.add(venta)
    db.session.flush()  # asigna id_venta sin cerrar la transaccion todavia

    for producto, cantidad, subtotal in lineas_validadas:
        detalle = DetalleVenta(
            id_venta=venta.id_venta,
            id_producto=producto.id_producto,
            cantidad=cantidad,
            precio_unitario=producto.precio_venta,
            subtotal=subtotal,
        )
        db.session.add(detalle)

        stock_anterior = producto.stock_actual
        producto.stock_actual = stock_anterior - cantidad

        movimiento = MovimientoStock(
            id_producto=producto.id_producto,
            id_usuario=usuario_id,
            tipo_movimiento='salida',
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_posterior=producto.stock_actual,
            motivo=f'Venta #{venta.id_venta}',
        )
        db.session.add(movimiento)

    db.session.commit()
    return venta


def obtener_venta_de_empresa(venta_id, empresa_id):
    return Venta.query.filter_by(id_venta=venta_id, id_empresa=empresa_id).first()


def listar_ventas(empresa_id, rango=None, desde=None, hasta=None):
    query = Venta.query.filter_by(id_empresa=empresa_id)
    ahora = datetime.utcnow()

    if rango == 'hoy':
        inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Venta.fecha >= inicio_dia)
    elif rango == '7dias':
        query = query.filter(Venta.fecha >= ahora - timedelta(days=7))
    elif rango == 'mes':
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Venta.fecha >= inicio_mes)
    elif rango == 'personalizado' and desde and hasta:
        try:
            fecha_desde = datetime.strptime(desde, '%Y-%m-%d')
            fecha_hasta = datetime.strptime(hasta, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Venta.fecha >= fecha_desde, Venta.fecha < fecha_hasta)
        except ValueError:
            pass  # fechas mal formadas: se ignora el filtro, se muestran todas

    return query.order_by(Venta.fecha.desc())
