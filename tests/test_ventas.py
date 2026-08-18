import pytest

from database.db import db as _db
from models.producto import Producto
from services.ventas_service import registrar_venta


def _crear_producto_directo(empresa_id, sku, stock_actual, precio_venta=200):
    producto = Producto(
        id_empresa=empresa_id, nombre=f'Producto {sku}', sku=sku,
        precio_compra=100, precio_venta=precio_venta,
        stock_actual=stock_actual, stock_minimo=5,
    )
    _db.session.add(producto)
    _db.session.commit()
    return producto


def test_venta_descuenta_stock_y_calcula_total_correctamente(app, usuario_empresa):
    with app.app_context():
        producto = _crear_producto_directo(usuario_empresa['id_empresa'], 'V-001', stock_actual=10)

        venta = registrar_venta(
            usuario_empresa['id_empresa'], usuario_empresa['id_usuario'],
            [{'producto_id': producto.id_producto, 'cantidad': 3}],
        )

        producto_actualizado = _db.session.get(Producto, producto.id_producto)
        assert producto_actualizado.stock_actual == 7          # 10 - 3
        assert float(venta.total) == 600.0                     # 3 x $200


def test_venta_rechaza_stock_insuficiente_y_no_modifica_nada(app, usuario_empresa):
    with app.app_context():
        producto = _crear_producto_directo(usuario_empresa['id_empresa'], 'V-002', stock_actual=2)

        with pytest.raises(ValueError):
            registrar_venta(
                usuario_empresa['id_empresa'], usuario_empresa['id_usuario'],
                [{'producto_id': producto.id_producto, 'cantidad': 5}],
            )

        # El stock NO debe haber cambiado: la venta se rechazo por completo
        producto_actualizado = _db.session.get(Producto, producto.id_producto)
        assert producto_actualizado.stock_actual == 2


def test_venta_sin_productos_es_rechazada(app, usuario_empresa):
    with app.app_context():
        with pytest.raises(ValueError):
            registrar_venta(usuario_empresa['id_empresa'], usuario_empresa['id_usuario'], [])
