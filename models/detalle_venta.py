from database.db import db


class DetalleVenta(db.Model):
    __tablename__ = 'detalle_ventas'

    id_detalle = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    # precio_unitario y subtotal quedan "congelados" al momento de la venta:
    # si el precio del producto cambia despues, el historial no se altera.
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    venta = db.relationship('Venta', backref='detalles')
    producto = db.relationship('Producto', backref='detalle_ventas')

    def __repr__(self):
        return f'<DetalleVenta venta={self.id_venta} producto={self.id_producto}>'
