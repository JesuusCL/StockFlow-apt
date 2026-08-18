from datetime import datetime

from database.db import db


class Producto(db.Model):
    __tablename__ = 'productos'

    id_producto = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresas.id_empresa'), nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'), nullable=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    sku = db.Column(db.String(50), nullable=False)
    precio_compra = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock_actual = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    estado = db.Column(db.Enum('activo', 'inactivo', name='producto_estado_enum'),
                        nullable=False, default='activo')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    empresa = db.relationship('Empresa', backref='productos')
    categoria = db.relationship('Categoria', backref='productos')

    @property
    def stock_bajo(self):
        """True si el stock actual esta en o por debajo del minimo configurado."""
        return self.stock_actual <= self.stock_minimo

    def __repr__(self):
        return f'<Producto {self.sku} - {self.nombre}>'
