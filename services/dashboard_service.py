import math
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


def ventas_recientes(empresa_id, limite=6):
    """Ultimas ventas de la empresa para el panel de actividad reciente.

    Devuelve una lista de diccionarios listos para mostrar (en la plantilla
    o como JSON para la actualizacion automatica del panel).
    """
    from services.formato_service import formato_clp

    ventas = (
        Venta.query
        .filter_by(id_empresa=empresa_id)
        .order_by(Venta.fecha.desc(), Venta.id_venta.desc())
        .limit(limite)
        .all()
    )

    actividad = []
    for venta in ventas:
        nombres = [d.producto.nombre for d in venta.detalles if d.producto is not None]
        if not nombres:
            titulo = f'Venta #{venta.id_venta}'
        elif len(nombres) == 1:
            titulo = nombres[0]
        else:
            titulo = f'{nombres[0]} y {len(nombres) - 1} mas'

        actividad.append({
            'id': venta.id_venta,
            'titulo': titulo,
            'unidades': venta.cantidad_productos,
            'fecha': venta.fecha.strftime('%d/%m/%Y') + ' · ' + venta.fecha.strftime('%H:%M') if venta.fecha else '',
            'total': formato_clp(venta.total),
            'estado': venta.estado,
        })

    return actividad


# ------------------------------------------------------------------
# Mapa de calor: ventas por dia de la semana y franja horaria
# ------------------------------------------------------------------
DIAS_SEMANA = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
DIAS_SEMANA_NOMBRE = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']

# (etiqueta, hora_inicio, hora_fin) en hora de Chile
FRANJAS_HORARIAS = [
    ('09-12', 9, 12),
    ('12-15', 12, 15),
    ('15-18', 15, 18),
    ('18-21', 18, 21),
]
FRANJA_FUERA_HORARIO = '21-09'


def _zona_chile():
    """Zona horaria de Chile. Las fechas se guardan en UTC, asi que hay que
    convertirlas para que las franjas coincidan con la hora local.
    Si el sistema no tiene la base de zonas horarias, se usa UTC-3 fijo."""
    from datetime import timezone
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo('America/Santiago')
    except Exception:
        return timezone(timedelta(hours=-3))


def mapa_calor_ventas(empresa_id, semanas=4):
    """Suma de ventas completadas de las ultimas `semanas`, agrupadas por
    dia de la semana (columnas L..D) y franja horaria (filas).

    'nivel' de cada celda va de 0 (sin ventas) a 5 (la celda con mas ventas).
    """
    from datetime import timezone
    from services.formato_service import formato_clp

    zona = _zona_chile()
    desde = datetime.utcnow() - timedelta(weeks=semanas)

    ventas = (
        db.session.query(Venta.fecha, Venta.total)
        .filter(
            Venta.id_empresa == empresa_id,
            Venta.estado == 'completada',
            Venta.fecha >= desde,
        )
        .all()
    )

    etiquetas = [f[0] for f in FRANJAS_HORARIAS] + [FRANJA_FUERA_HORARIO]
    totales = {e: [0.0] * 7 for e in etiquetas}
    cantidades = {e: [0] * 7 for e in etiquetas}

    for fecha, total in ventas:
        if fecha is None:
            continue
        local = fecha.replace(tzinfo=timezone.utc).astimezone(zona)
        franja = FRANJA_FUERA_HORARIO
        for etiqueta, inicio, fin in FRANJAS_HORARIAS:
            if inicio <= local.hour < fin:
                franja = etiqueta
                break
        dia = local.weekday()  # 0 = lunes
        totales[franja][dia] += float(total or 0)
        cantidades[franja][dia] += 1

    # La fila "fuera de horario" solo se muestra si tiene ventas
    if not any(cantidades[FRANJA_FUERA_HORARIO]):
        etiquetas.remove(FRANJA_FUERA_HORARIO)

    maximo = max((t for e in etiquetas for t in totales[e]), default=0)

    filas = []
    for etiqueta in etiquetas:
        celdas = []
        for dia in range(7):
            total = totales[etiqueta][dia]
            cantidad = cantidades[etiqueta][dia]
            if cantidad == 0 or maximo <= 0:
                nivel = 0
            else:
                # 1..5 proporcional a la celda con mas ventas
                nivel = max(1, min(5, math.ceil(total / maximo * 5)))
            nombre = f'{DIAS_SEMANA_NOMBRE[dia]} {etiqueta} h'
            if cantidad == 0:
                titulo = f'{nombre}: sin ventas'
            else:
                plural = 'venta' if cantidad == 1 else 'ventas'
                titulo = f'{nombre}: {formato_clp(total)} ({cantidad} {plural})'
            celdas.append({'nivel': nivel, 'titulo': titulo})
        filas.append({'franja': etiqueta, 'celdas': celdas})

    return {
        'dias': DIAS_SEMANA,
        'filas': filas,
        'semanas': semanas,
        'hay_ventas': maximo > 0,
    }
