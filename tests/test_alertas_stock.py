"""Pruebas del aviso de stock bajo (endpoint JSON) y del correo de alerta."""
from datetime import datetime, timedelta

import pytest

from app import create_app
from config import TestConfig
from database.db import db
from models.usuario import Usuario
from models.empresa import Empresa
from models.producto import Producto
from models.alerta_stock_envio import AlertaStockEnvio
from services import email_service

CORREO = 'je.oyarzunr@duocuc.cl'
CLAVE = 'Clave12345'
URL = '/inventario/alertas/estado'


def _crear_empresa(nombre_usuario, correo, nombre_empresa, productos):
    usuario = Usuario(nombre_usuario=nombre_usuario, correo=correo, nombre_completo=nombre_usuario)
    usuario.set_password(CLAVE)
    db.session.add(usuario)
    db.session.commit()

    empresa = Empresa(id_usuario=usuario.id_usuario, nombre_empresa=nombre_empresa, tipo_negocio='pyme')
    db.session.add(empresa)
    db.session.commit()

    for nombre, sku, stock, minimo in productos:
        db.session.add(Producto(
            id_empresa=empresa.id_empresa, nombre=nombre, sku=sku,
            precio_compra=1000, precio_venta=2000, stock_actual=stock, stock_minimo=minimo,
        ))
    db.session.commit()
    return empresa.id_empresa


@pytest.fixture
def app_alertas():
    app = create_app(TestConfig)
    email_service.OUTBOX.clear()

    with app.app_context():
        db.create_all()
        app.config['ID_EMPRESA_PRUEBA'] = _crear_empresa(
            'admin', CORREO, 'Pyme Prueba',
            [('Polera', 'POL-1', 1, 5), ('Short', 'SHO-1', 50, 5)],
        )
        # Otra empresa con stock bajo: nunca debe mezclarse con la primera.
        _crear_empresa('otro', 'otro@empresa.cl', 'Otra Pyme', [('Gorro', 'GOR-1', 0, 5)])

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def cliente(app_alertas):
    client = app_alertas.test_client()
    client.post('/login', data={'correo': CORREO, 'password': CLAVE})
    return client


def test_el_endpoint_requiere_sesion(app_alertas):
    respuesta = app_alertas.test_client().get(URL)

    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers['Location']


def test_devuelve_solo_los_productos_con_stock_bajo_de_la_empresa(cliente):
    datos = cliente.get(URL).get_json()

    assert datos['count'] == 1
    assert datos['productos'][0]['nombre'] == 'Polera'


def test_envia_un_correo_con_el_resumen(cliente):
    cliente.get(URL)

    assert len(email_service.OUTBOX) == 1
    correo = email_service.OUTBOX[0]
    assert correo['to'] == [CORREO]
    assert '1 producto' in correo['subject']
    assert 'Polera' in correo['text']
    assert 'Gorro' not in correo['text']


def test_no_repite_el_correo_dentro_del_intervalo(cliente):
    cliente.get(URL)
    cliente.get(URL)
    cliente.get(URL)

    assert len(email_service.OUTBOX) == 1


def test_vuelve_a_enviar_pasado_el_intervalo(app_alertas, cliente):
    cliente.get(URL)

    with app_alertas.app_context():
        registro = db.session.get(AlertaStockEnvio, app_alertas.config['ID_EMPRESA_PRUEBA'])
        registro.ultimo_envio = datetime.utcnow() - timedelta(hours=2)
        db.session.commit()

    cliente.get(URL)

    assert len(email_service.OUTBOX) == 2


def test_incluye_los_correos_adicionales_configurados(app_alertas, cliente):
    app_alertas.config['ALERTA_STOCK_CORREOS_EXTRA'] = ['otro.correo@duocuc.cl']

    cliente.get(URL)

    assert email_service.OUTBOX[0]['to'] == [CORREO, 'otro.correo@duocuc.cl']


def test_sin_productos_bajo_no_avisa_ni_envia_correo(app_alertas, cliente):
    with app_alertas.app_context():
        Producto.query.filter_by(sku='POL-1').update({'stock_actual': 20})
        db.session.commit()

    datos = cliente.get(URL).get_json()

    assert datos['count'] == 0
    assert len(email_service.OUTBOX) == 0
