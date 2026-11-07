from datetime import datetime

from database.db import db


class CodigoVerificacion(db.Model):
    """Codigo de un solo uso enviado por correo para completar el inicio de sesion."""
    __tablename__ = 'codigos_verificacion'

    id_codigo = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    codigo_hash = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    intentos = db.Column(db.Integer, nullable=False, default=0)
    usado = db.Column(db.Boolean, nullable=False, default=False)

    usuario = db.relationship('Usuario', backref='codigos_verificacion')

    def __repr__(self):
        return f'<CodigoVerificacion usuario={self.id_usuario} usado={self.usado}>'
