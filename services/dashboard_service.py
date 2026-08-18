from datetime import datetime, timedelta

from database.db import db
from models.producto import Producto
from models.venta import Venta


def obtener_resumen(empresa_id):
    ahora = datetime.utcnow()
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    ventas_hoy_total = (
        db.session.query(db.func.coalesce(db.func.sum(Venta.total), 0))
        .filter(Venta.id_empresa == empresa_id, Venta.fecha >= inicio_dia)
        .scalar()
    )

    total_productos = Producto.query.filter_by(id_empresa=empresa_id, estado='activo').count()

    stock_total = (
        db.session.query(db.func.coalesce(db.func.sum(Producto.stock_actual), 0))
        .filter(Producto.id_empresa == empresa_id, Producto.estado == 'activo')
        .scalar()
    )

    stock_bajo_count = (
        Producto.query
        .filter_by(id_empresa=empresa_id, estado='activo')
        .filter(Producto.stock_actual <= Producto.stock_minimo)
        .count()
    )

    return {
        'ventas_hoy': float(ventas_hoy_total),
        'total_productos': total_productos,
        'stock_total': int(stock_total),
        'stock_bajo_count': stock_bajo_count,
    }


def ventas_ultimos_dias(empresa_id, dias=7):
    """Devuelve (etiquetas, valores) para graficar la evolucion de ventas."""
    ahora = datetime.utcnow()
    inicio = (ahora - timedelta(days=dias - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    filas = (
        db.session.query(
            db.func.date(Venta.fecha).label('fecha'),
            db.func.sum(Venta.total).label('total'),
        )
        .filter(Venta.id_empresa == empresa_id, Venta.fecha >= inicio)
        .group_by(db.func.date(Venta.fecha))
        .all()
    )

    mapa_ventas = {str(fila.fecha): float(fila.total) for fila in filas}

    etiquetas, valores = [], []
    for i in range(dias):
        dia = (inicio + timedelta(days=i)).date()
        etiquetas.append(dia.strftime('%d-%m'))
        valores.append(mapa_ventas.get(str(dia), 0))

    return etiquetas, valores
