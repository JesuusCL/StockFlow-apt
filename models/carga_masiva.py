from datetime import datetime

from database.db import db


class CargaMasiva(db.Model):
    __tablename__ = 'cargas_masivas'

    id_carga = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresas.id_empresa'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    total_filas = db.Column(db.Integer, nullable=False, default=0)
    filas_exitosas = db.Column(db.Integer, nullable=False, default=0)
    filas_con_error = db.Column(db.Integer, nullable=False, default=0)
    estado = db.Column(db.Enum('completado', 'con_errores', 'fallido', name='carga_estado_enum'),
                        nullable=False, default='completado')
    fecha_carga = db.Column(db.DateTime, default=datetime.utcnow)

    empresa = db.relationship('Empresa', backref='cargas_masivas')
    usuario = db.relationship('Usuario', backref='cargas_masivas')
    errores = db.relationship('CargaMasivaError', backref='carga', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CargaMasiva {self.id_carga} - {self.nombre_archivo}>'


class CargaMasivaError(db.Model):
    __tablename__ = 'cargas_masivas_errores'

    id_error = db.Column(db.Integer, primary_key=True)
    id_carga = db.Column(db.Integer, db.ForeignKey('cargas_masivas.id_carga'), nullable=False)
    numero_fila = db.Column(db.Integer, nullable=False)
    motivo_error = db.Column(db.String(255), nullable=False)
