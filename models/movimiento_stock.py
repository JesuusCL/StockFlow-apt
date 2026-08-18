from datetime import datetime

from database.db import db


class MovimientoStock(db.Model):
    __tablename__ = 'movimientos_stock'

    id_movimiento = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    tipo_movimiento = db.Column(db.Enum('entrada', 'salida', name='tipo_movimiento_enum'),
                                 nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    stock_anterior = db.Column(db.Integer, nullable=False)
    stock_posterior = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship('Producto', backref='movimientos')
    usuario = db.relationship('Usuario', backref='movimientos_stock')

    def __repr__(self):
        return f'<MovimientoStock {self.tipo_movimiento} {self.cantidad} - producto {self.id_producto}>'
