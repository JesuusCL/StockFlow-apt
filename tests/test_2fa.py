"""Pruebas del inicio de sesion con codigo enviado al correo (2FA)."""
import re
from datetime import datetime, timedelta

import pytest

from app import create_app
from config import TestConfig
from database.db import db
from models.usuario import Usuario
from models.codigo_verificacion import CodigoVerificacion
from services import email_service

CORREO = 'je.oyarzunr@duocuc.cl'
CLAVE = 'Clave12345'


@pytest.fixture
def app_2fa():
    app = create_app(TestConfig)
    app.config['LOGIN_2FA_ENABLED'] = True
    email_service.OUTBOX.clear()

    with app.app_context():
        db.create_all()
        usuario = Usuario(nombre_usuario='admin', correo=CORREO, nombre_completo='Admin Prueba')
        usuario.set_password(CLAVE)
        db.session.add(usuario)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


def _paso_1(client, siguiente=None):
    url = '/login' + (f'?next={siguiente}' if siguiente else '')
    return client.post(url, data={'correo': CORREO, 'password': CLAVE})


def _codigo_enviado():
    return re.search(r'\b(\d{6})\b', email_service.OUTBOX[-1]['text']).group(1)


def _esta_autenticado(client):
    respuesta = client.get('/productos/')
    return '/login' not in (respuesta.headers.get('Location') or '')


def test_contrasena_correcta_no_inicia_sesion_hasta_ingresar_el_codigo(app_2fa):
    client = app_2fa.test_client()

    respuesta = _paso_1(client)

    assert respuesta.status_code == 302
    assert '/verificar-codigo' in respuesta.headers['Location']
    assert len(email_service.OUTBOX) == 1
    assert email_service.OUTBOX[0]['to'] == [CORREO]
    assert not _esta_autenticado(client)


def test_codigo_correcto_inicia_sesion(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client)

    respuesta = client.post('/verificar-codigo', data={'codigo': _codigo_enviado()})

    assert respuesta.status_code == 302
    assert _esta_autenticado(client)


def test_codigo_incorrecto_no_inicia_sesion(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client)

    respuesta = client.post('/verificar-codigo', data={'codigo': '000000' if _codigo_enviado() != '000000' else '111111'})

    assert respuesta.status_code == 200
    assert b'Codigo incorrecto' in respuesta.data
    assert not _esta_autenticado(client)


def test_el_codigo_se_guarda_con_hash_y_no_en_texto_plano(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client)
    codigo = _codigo_enviado()

    with app_2fa.app_context():
        registro = CodigoVerificacion.query.one()
        assert registro.codigo_hash != codigo
        assert codigo not in registro.codigo_hash


def test_tras_5_intentos_fallidos_el_codigo_correcto_ya_no_sirve(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client)
    correcto = _codigo_enviado()
    incorrecto = '000000' if correcto != '000000' else '111111'

    for _ in range(5):
        client.post('/verificar-codigo', data={'codigo': incorrecto})
    respuesta = client.post('/verificar-codigo', data={'codigo': correcto})

    assert respuesta.status_code == 200
    assert b'Solicita un codigo nuevo' in respuesta.data
    assert not _esta_autenticado(client)


def test_codigo_vencido_es_rechazado(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client)
    codigo = _codigo_enviado()

    with app_2fa.app_context():
        registro = CodigoVerificacion.query.one()
        registro.fecha_expiracion = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

    respuesta = client.post('/verificar-codigo', data={'codigo': codigo})

    assert b'vencio' in respuesta.data
    assert not _esta_autenticado(client)


def test_reenviar_inmediatamente_respeta_la_espera(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client)

    client.post('/reenviar-codigo')

    assert len(email_service.OUTBOX) == 1  # no se mando un segundo correo


def test_reenviar_genera_codigo_nuevo_e_invalida_el_anterior(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client)
    codigo_viejo = _codigo_enviado()

    with app_2fa.app_context():  # simula que ya paso el tiempo de espera
        registro = CodigoVerificacion.query.one()
        registro.fecha_creacion = datetime.utcnow() - timedelta(minutes=2)
        db.session.commit()

    client.post('/reenviar-codigo')
    assert len(email_service.OUTBOX) == 2
    codigo_nuevo = _codigo_enviado()

    if codigo_viejo != codigo_nuevo:
        client.post('/verificar-codigo', data={'codigo': codigo_viejo})
        assert not _esta_autenticado(client)

    client.post('/verificar-codigo', data={'codigo': codigo_nuevo})
    assert _esta_autenticado(client)


def test_verificar_codigo_sin_pasar_por_el_login_redirige_al_login(app_2fa):
    client = app_2fa.test_client()

    respuesta = client.get('/verificar-codigo')

    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers['Location']


def test_credenciales_incorrectas_no_envian_codigo(app_2fa):
    client = app_2fa.test_client()

    respuesta = client.post('/login', data={'correo': CORREO, 'password': 'otra-clave'})

    assert respuesta.status_code == 200
    assert len(email_service.OUTBOX) == 0


def test_la_redireccion_next_solo_acepta_rutas_internas(app_2fa):
    client = app_2fa.test_client()
    _paso_1(client, siguiente='//sitio-malicioso.com')

    respuesta = client.post('/verificar-codigo', data={'codigo': _codigo_enviado()})

    assert respuesta.status_code == 302
    assert 'sitio-malicioso' not in respuesta.headers['Location']


def test_con_2fa_desactivado_el_login_es_directo(app_2fa):
    app_2fa.config['LOGIN_2FA_ENABLED'] = False
    client = app_2fa.test_client()

    respuesta = _paso_1(client)

    assert respuesta.status_code == 302
    assert '/verificar-codigo' not in respuesta.headers['Location']
    assert len(email_service.OUTBOX) == 0
    assert _esta_autenticado(client)
