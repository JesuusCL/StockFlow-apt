import secrets
from datetime import datetime, timedelta

from flask import current_app
from markupsafe import escape
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import db
from models.codigo_verificacion import CodigoVerificacion
from services import email_service


def enmascarar_correo(correo):
    """je.oyarzunr@duocuc.cl -> j***@duocuc.cl (para no mostrar el correo completo en pantalla)."""
    local, _, dominio = correo.partition('@')
    return f"{local[:1]}{'*' * max(len(local) - 1, 2)}@{dominio}"


def _ultimo_codigo(usuario):
    return (CodigoVerificacion.query
            .filter_by(id_usuario=usuario.id_usuario)
            .order_by(CodigoVerificacion.id_codigo.desc())
            .first())


def segundos_para_reenvio(usuario):
    """Segundos que faltan para poder pedir otro codigo (0 si ya se puede)."""
    ultimo = _ultimo_codigo(usuario)
    if ultimo is None:
        return 0
    espera = current_app.config['CODIGO_2FA_REENVIO_SEGUNDOS']
    transcurrido = (datetime.utcnow() - ultimo.fecha_creacion).total_seconds()
    return max(0, int(espera - transcurrido))


def generar_y_enviar_codigo(usuario):
    """
    Genera un codigo de 6 digitos, lo guarda con hash (nunca en texto plano) y
    lo envia al correo del usuario. Invalida los codigos anteriores sin usar.
    Devuelve True si el correo se envio correctamente.
    """
    minutos = current_app.config['CODIGO_2FA_MINUTOS']

    CodigoVerificacion.query.filter_by(id_usuario=usuario.id_usuario, usado=False).update({'usado': True})

    codigo = f'{secrets.randbelow(10 ** 6):06d}'
    ahora = datetime.utcnow()
    registro = CodigoVerificacion(
        id_usuario=usuario.id_usuario,
        codigo_hash=generate_password_hash(codigo),
        fecha_creacion=ahora,
        fecha_expiracion=ahora + timedelta(minutes=minutos),
    )
    db.session.add(registro)
    db.session.commit()

    texto = (
        f'Hola {usuario.nombre_completo},\n\n'
        f'Tu codigo de verificacion para ingresar a StockFlow es: {codigo}\n\n'
        f'Vence en {minutos} minutos. Si no fuiste tu quien intento iniciar sesion, '
        f'ignora este correo y cambia tu contrasena.\n\n'
        f'-- StockFlow'
    )
    html = (
        f'<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;color:#222">'
        f'<h2 style="color:#16233E">StockFlow</h2>'
        f'<p>Hola {escape(usuario.nombre_completo)},</p>'
        f'<p>Tu codigo de verificacion para ingresar es:</p>'
        f'<p style="font-size:32px;letter-spacing:8px;font-weight:bold;color:#16233E">{codigo}</p>'
        f'<p>Vence en {minutos} minutos. Si no fuiste tu quien intento iniciar sesion, '
        f'ignora este correo y cambia tu contrasena.</p></div>'
    )

    enviado = email_service.enviar_correo([usuario.correo], 'Tu codigo de acceso a StockFlow', texto, html)
    if not enviado:
        registro.usado = True  # un codigo que nunca llego no debe quedar valido
        db.session.commit()
    return enviado


def verificar_codigo(usuario, codigo_ingresado):
    """
    Comprueba el codigo ingresado. Devuelve (ok, motivo, intentos_restantes).
    motivo: 'ok' | 'sin_codigo' | 'expirado' | 'bloqueado' | 'incorrecto'
    """
    maximo = current_app.config['CODIGO_2FA_MAX_INTENTOS']

    registro = (CodigoVerificacion.query
                .filter_by(id_usuario=usuario.id_usuario, usado=False)
                .order_by(CodigoVerificacion.id_codigo.desc())
                .first())

    if registro is None:
        return False, 'sin_codigo', 0
    if registro.fecha_expiracion < datetime.utcnow():
        return False, 'expirado', 0
    if registro.intentos >= maximo:
        return False, 'bloqueado', 0

    if check_password_hash(registro.codigo_hash, (codigo_ingresado or '').strip()):
        registro.usado = True
        db.session.commit()
        return True, 'ok', maximo

    registro.intentos += 1
    db.session.commit()
    restantes = maximo - registro.intentos
    return False, ('bloqueado' if restantes <= 0 else 'incorrecto'), max(restantes, 0)
