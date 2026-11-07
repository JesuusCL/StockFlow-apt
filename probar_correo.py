"""
Prueba de envio de correo de StockFlow (no usa la base de datos ni el sitio).

Como usarlo (con el entorno virtual activado, en la carpeta del proyecto):
    python probar_correo.py
    python probar_correo.py otro_destino@correo.cl     (opcional: otro destinatario)

Lee el mismo archivo .env que usa el sistema y muestra el motivo exacto si falla.
"""
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

from dotenv import load_dotenv

carpeta = os.path.abspath(os.path.dirname(__file__))
ruta_env = os.path.join(carpeta, '.env')
print(f'Buscando .env en: {ruta_env}  ->  {"ENCONTRADO" if os.path.exists(ruta_env) else "NO EXISTE"}')
load_dotenv(ruta_env)

servidor = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
puerto = int(os.environ.get('MAIL_PORT', '587'))
usuario = os.environ.get('MAIL_USERNAME', '')
clave = os.environ.get('MAIL_PASSWORD', '')
destino = sys.argv[1] if len(sys.argv) > 1 else 'je.oyarzunr@duocuc.cl'

print(f'MAIL_SERVER   = {servidor}')
print(f'MAIL_PORT     = {puerto}')
print(f'MAIL_USERNAME = {usuario or "(VACIO)"}')
print(f'MAIL_PASSWORD = {"(" + str(len(clave)) + " caracteres)" if clave else "(VACIA)"}')
print(f'Destino       = {destino}')
print('-' * 50)

if not usuario or not clave:
    print('PROBLEMA: falta MAIL_USERNAME o MAIL_PASSWORD en el .env.')
    print('Sin eso el sistema NO envia correos (solo los imprime en la terminal).')
    sys.exit(1)

if ' ' in clave:
    print('AVISO: MAIL_PASSWORD tiene espacios. La contrasena de aplicacion va SIN espacios (16 letras juntas).')

mensaje = EmailMessage()
mensaje['Subject'] = 'Prueba de correo - StockFlow'
mensaje['From'] = os.environ.get('MAIL_DEFAULT_SENDER') or f'StockFlow <{usuario}>'
mensaje['To'] = destino
mensaje.set_content('Si lees esto, el envio de correos de StockFlow funciona correctamente.')

try:
    with smtplib.SMTP(servidor, puerto, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(usuario, clave)
        smtp.send_message(mensaje)
    print('LISTO: correo enviado. Revisa la bandeja de entrada (y spam) de', destino)
except smtplib.SMTPAuthenticationError as error:
    print('FALLO DE AUTENTICACION (Gmail rechazo usuario/contrasena).')
    print('Causas tipicas: usaste la contrasena normal en vez de la "contrasena de aplicacion",')
    print('la cuenta no tiene la verificacion en 2 pasos activada, o MAIL_USERNAME esta mal escrito.')
    print('Detalle:', error)
except (smtplib.SMTPException, OSError) as error:
    print('FALLO AL ENVIAR (conexion o servidor).')
    print('Si dice "timed out" o "getaddrinfo": revisa internet / firewall / antivirus.')
    print('Detalle:', error)
