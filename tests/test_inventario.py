from database.db import db as _db
from models.producto import Producto
from models.movimiento_stock import MovimientoStock
from services.inventario_service import registrar_entrada


def test_entrada_stock_actualiza_producto_y_genera_movimiento(app, usuario_empresa):
    with app.app_context():
        producto = Producto(
            id_empresa=usuario_empresa['id_empresa'], nombre='Producto Stock', sku='INV-001',
            precio_compra=100, precio_venta=200, stock_actual=5, stock_minimo=5,
        )
        _db.session.add(producto)
        _db.session.commit()

        registrar_entrada(producto, 20, usuario_empresa['id_usuario'], motivo='Reposicion de prueba')

        producto_actualizado = _db.session.get(Producto, producto.id_producto)
        assert producto_actualizado.stock_actual == 25

        movimiento = MovimientoStock.query.filter_by(id_producto=producto.id_producto).first()
        assert movimiento is not None
        assert movimiento.tipo_movimiento == 'entrada'
        assert movimiento.stock_anterior == 5
        assert movimiento.stock_posterior == 25
        assert movimiento.motivo == 'Reposicion de prueba'


def test_stock_bajo_se_resuelve_automaticamente_tras_entrada(app, usuario_empresa):
    with app.app_context():
        producto = Producto(
            id_empresa=usuario_empresa['id_empresa'], nombre='Producto Bajo', sku='INV-002',
            precio_compra=100, precio_venta=200, stock_actual=2, stock_minimo=5,
        )
        _db.session.add(producto)
        _db.session.commit()

        assert producto.stock_bajo is True

        registrar_entrada(producto, 10, usuario_empresa['id_usuario'])

        assert producto.stock_bajo is False
