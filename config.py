import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


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


class TestConfig(Config):
    """Configuracion usada exclusivamente por la suite de pruebas (Fase 12).

    Usa SQLite en memoria: no requiere MySQL corriendo, es rapida, y cada
    prueba arranca con una base de datos limpia y aislada.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # simplifica el envio de formularios en las pruebas
    SECRET_KEY = 'clave-secreta-solo-para-pruebas'
