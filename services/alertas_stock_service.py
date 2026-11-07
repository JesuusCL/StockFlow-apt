import threading
from datetime import datetime, timedelta

from flask import current_app
from markupsafe import escape

from database.db import db
from models.alerta_stock_envio import AlertaStockEnvio
from services import email_service


def _construir_mensaje(nombre_empresa, productos):
    lineas_texto = [
        f'- {p.nombre} (SKU {p.sku}): stock {p.stock_actual}, minimo {p.stock_minimo}'
        for p in productos
    ]
    texto = (
        f'Hola,\n\nEn {nombre_empresa} hay {len(productos)} producto(s) con stock bajo. '
        f'Revisa el stock y repon lo necesario:\n\n' + '\n'.join(lineas_texto) +
        '\n\n-- StockFlow'
    )
    filas_html = ''.join(
        f'<tr><td style="padding:4px 8px">{escape(p.nombre)}</td>'
        f'<td style="padding:4px 8px">{escape(p.sku)}</td>'
        f'<td style="padding:4px 8px;text-align:right">{p.stock_actual}</td>'
        f'<td style="padding:4px 8px;text-align:right">{p.stock_minimo}</td></tr>'
        for p in productos
    )
    html = (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#222">'
        '<h2 style="color:#16233E">Stock bajo</h2>'
        f'<p>En <strong>{escape(nombre_empresa)}</strong> hay {len(productos)} producto(s) con stock bajo. '
        'Revisa el stock y repon lo necesario.</p>'
        '<table style="border-collapse:collapse;width:100%;font-size:14px" border="1" bordercolor="#ddd">'
        '<tr style="background:#f1f3f5"><th style="padding:4px 8px;text-align:left">Producto</th>'
        '<th style="padding:4px 8px;text-align:left">SKU</th>'
        '<th style="padding:4px 8px">Stock</th><th style="padding:4px 8px">Minimo</th></tr>'
        f'{filas_html}</table></div>'
    )
    return texto, html


def _liberar_intervalo(id_empresa):
    """Si el correo no pudo enviarse, se borra el registro para reintentar en la
    proxima consulta, en vez de esperar una hora completa sin haber avisado."""
    registro = db.session.get(AlertaStockEnvio, id_empresa)
    if registro is not None:
        db.session.delete(registro)
        db.session.commit()


def notificar_por_correo_si_corresponde(usuario, empresa, productos_bajo):
    """
    Envia por correo el resumen de productos con stock bajo, pero como maximo
    una vez cada ALERTA_STOCK_CORREO_MINUTOS por empresa (para no llenar la
    bandeja). Devuelve True si se disparo un envio.
    """
    if not productos_bajo:
        return False

    intervalo = timedelta(minutes=current_app.config['ALERTA_STOCK_CORREO_MINUTOS'])
    ahora = datetime.utcnow()

    registro = db.session.get(AlertaStockEnvio, empresa.id_empresa)
    if registro is not None and ahora - registro.ultimo_envio < intervalo:
        return False

    # Se registra el envio ANTES de mandarlo: si el usuario tiene dos pestanas
    # abiertas, la segunda ya ve el registro y no duplica el correo.
    if registro is None:
        db.session.add(AlertaStockEnvio(id_empresa=empresa.id_empresa, ultimo_envio=ahora))
    else:
        registro.ultimo_envio = ahora
    db.session.commit()

    destinatarios = [usuario.correo] + [
        c for c in current_app.config['ALERTA_STOCK_CORREOS_EXTRA'] if c != usuario.correo
    ]
    texto, html = _construir_mensaje(empresa.nombre_empresa, productos_bajo)
    asunto = f'StockFlow: {len(productos_bajo)} producto(s) con stock bajo'

    id_empresa = empresa.id_empresa

    if current_app.config.get('TESTING'):
        if not email_service.enviar_correo(destinatarios, asunto, texto, html):
            _liberar_intervalo(id_empresa)
        return True

    # Fuera de pruebas se envia en segundo plano para que la pagina no espere al servidor de correo.
    app = current_app._get_current_object()

    def _enviar():
        with app.app_context():
            if not email_service.enviar_correo(destinatarios, asunto, texto, html):
                _liberar_intervalo(id_empresa)

    threading.Thread(target=_enviar, daemon=True).start()
    return True
