from datetime import datetime

from database.db import db


class Venta(db.Model):
    __tablename__ = 'ventas'

    id_venta = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresas.id_empresa'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    estado = db.Column(db.Enum('completada', 'anulada', name='venta_estado_enum'),
                        nullable=False, default='completada')

    empresa = db.relationship('Empresa', backref='ventas')
    usuario = db.relationship('Usuario', backref='ventas')

    @property
    def cantidad_productos(self):
        return sum(detalle.cantidad for detalle in self.detalles)

    def __repr__(self):
        return f'<Venta #{self.id_venta} - ${self.total}>'
