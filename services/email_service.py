import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app

# Durante las pruebas (TESTING=True) los correos no se envian: quedan en esta
# lista para que las pruebas automaticas puedan revisarlos.
OUTBOX = []


def enviar_correo(destinatarios, asunto, texto, html=None):
    """
    Envia un correo por SMTP. Devuelve True si se envio (o se simulo) y False si fallo.

    - TESTING: guarda el mensaje en OUTBOX y no se conecta a ningun servidor.
    - Sin MAIL_USERNAME configurado: imprime el mensaje en la consola de Flask
      (modo desarrollo, para poder probar el flujo sin una cuenta de correo).
    - Con MAIL_USERNAME y MAIL_PASSWORD: envia por SMTP (Gmail por defecto).
    """
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return False

    config = current_app.config

    if config.get('TESTING'):
        OUTBOX.append({'to': destinatarios, 'subject': asunto, 'text': texto, 'html': html})
        return True

    usuario_smtp = config.get('MAIL_USERNAME')
    if not usuario_smtp:
        print('\n' + '=' * 60)
        print('[StockFlow] MAIL_USERNAME no esta configurado: correo NO enviado, solo simulado.')
        print(f'Para: {", ".join(destinatarios)}')
        print(f'Asunto: {asunto}')
        print(texto)
        print('=' * 60 + '\n')
        return True

    mensaje = EmailMessage()
    mensaje['Subject'] = asunto
    mensaje['From'] = config['MAIL_DEFAULT_SENDER']
    mensaje['To'] = ', '.join(destinatarios)
    mensaje.set_content(texto)
    if html:
        mensaje.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT'], timeout=15) as servidor:
            if config.get('MAIL_USE_TLS', True):
                servidor.starttls(context=ssl.create_default_context())
            servidor.login(usuario_smtp, config.get('MAIL_PASSWORD', ''))
            servidor.send_message(mensaje)
        return True
    except (smtplib.SMTPException, OSError) as error:
        current_app.logger.error('No se pudo enviar el correo a %s: %s', destinatarios, error)
        return False
