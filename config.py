import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


def _env_bool(nombre, defecto=True):
    valor = os.environ.get(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in ('1', 'true', 'si', 'yes')


class Config:
    """Configuracion central de la aplicacion.

    Todos los valores sensibles se leen desde variables de entorno (.env),
    nunca deben quedar escritos directamente en este archivo.
    """

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-insegura-solo-para-desarrollo')

    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'Inventario_web')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

    # --- Seguridad de sesion (Fase 11) ---
    # La sesion expira sola tras 2 horas de inactividad.
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    # La cookie de sesion no es accesible via JavaScript (mitiga robo por XSS).
    SESSION_COOKIE_HTTPONLY = True
    # La cookie no se envia en peticiones de otros sitios (mitiga CSRF adicional).
    SESSION_COOKIE_SAMESITE = 'Lax'
    # En produccion (con HTTPS) esto deberia ser True. En desarrollo local
    # (http://127.0.0.1) debe quedar en False, o el navegador descarta la cookie.
    SESSION_COOKIE_SECURE = False

    # --- Correo saliente (codigos de verificacion y alertas de stock) ---
    # Todo se configura en el archivo .env (ver LEEME). Sin MAIL_USERNAME el
    # sistema NO envia correos reales: imprime el mensaje en la consola de
    # Flask, util solo para desarrollo.
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = _env_bool('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or (
        f'StockFlow <{MAIL_USERNAME}>' if MAIL_USERNAME else 'StockFlow <no-reply@stockflow.local>'
    )

    # --- Autenticacion por codigo enviado al correo ---
    LOGIN_2FA_ENABLED = _env_bool('LOGIN_2FA_ENABLED', True)
    CODIGO_2FA_MINUTOS = 5            # vigencia del codigo
    CODIGO_2FA_MAX_INTENTOS = 5       # intentos fallidos antes de pedir un codigo nuevo
    CODIGO_2FA_REENVIO_SEGUNDOS = 60  # espera minima entre un envio y el siguiente

    # --- Alertas de stock bajo ---
    # Cada cuantos minutos como maximo se manda el correo de stock bajo por empresa.
    ALERTA_STOCK_CORREO_MINUTOS = int(os.environ.get('ALERTA_STOCK_CORREO_MINUTOS', '60'))
    # Correos adicionales (separados por coma) que tambien reciben la alerta.
    ALERTA_STOCK_CORREOS_EXTRA = [
        c.strip() for c in os.environ.get('ALERTA_STOCK_CORREOS_EXTRA', '').split(',') if c.strip()
    ]


class TestConfig(Config):
    """Configuracion usada exclusivamente por la suite de pruebas (Fase 12).

    Usa SQLite en memoria: no requiere MySQL corriendo, es rapida, y cada
    prueba arranca con una base de datos limpia y aislada.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # simplifica el envio de formularios en las pruebas
    SECRET_KEY = 'clave-secreta-solo-para-pruebas'
    # Las pruebas existentes inician sesion solo con correo y contrasena; el
    # codigo por correo se prueba aparte (tests/test_2fa.py) activandolo a mano.
    LOGIN_2FA_ENABLED = False
    MAIL_USERNAME = ''
