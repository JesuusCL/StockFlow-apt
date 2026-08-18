import pytest

from app import create_app
from config import TestConfig
from database.db import db as _db
from models.usuario import Usuario
from models.empresa import Empresa


@pytest.fixture
def app():
    """Crea una instancia de la app con base de datos SQLite limpia por prueba."""
    aplicacion = create_app(TestConfig)
    with aplicacion.app_context():
        _db.create_all()
        yield aplicacion
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def usuario_empresa(app):
    """Crea un usuario con su empresa ya configurada. Devuelve sus datos como dict
    (no el objeto ORM, para evitar problemas de sesion fuera del contexto de la app)."""
    with app.app_context():
        usuario = Usuario(
            nombre_usuario='usuario_test',
            correo='usuario@test.com',
            nombre_completo='Usuario de Prueba',
        )
        usuario.set_password('Password123')
        _db.session.add(usuario)
        _db.session.commit()

        empresa = Empresa(
            id_usuario=usuario.id_usuario,
            nombre_empresa='Empresa de Prueba',
            tipo_negocio='pyme',
        )
        _db.session.add(empresa)
        _db.session.commit()

        return {
            'id_usuario': usuario.id_usuario,
            'id_empresa': empresa.id_empresa,
            'correo': 'usuario@test.com',
            'password': 'Password123',
        }


@pytest.fixture
def cliente_logueado(client, usuario_empresa):
    """Cliente de pruebas con sesion ya iniciada, listo para probar rutas privadas."""
    client.post('/login', data={
        'correo': usuario_empresa['correo'],
        'password': usuario_empresa['password'],
    }, follow_redirects=True)
    return client
