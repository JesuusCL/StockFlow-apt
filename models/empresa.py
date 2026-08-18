from datetime import datetime

from database.db import db


class Empresa(db.Model):
    __tablename__ = 'empresas'

    id_empresa = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'),
                            nullable=False, unique=True)
    nombre_empresa = db.Column(db.String(150), nullable=False)
    tipo_negocio = db.Column(db.Enum('pyme', 'empresa', name='tipo_negocio_enum'),
                              nullable=False)
    rut = db.Column(db.String(20), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(255), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # backref: permite acceder desde un objeto Usuario como current_user.empresa
    usuario = db.relationship('Usuario', backref=db.backref('empresa', uselist=False))

    def __repr__(self):
        return f'<Empresa {self.nombre_empresa}>'
