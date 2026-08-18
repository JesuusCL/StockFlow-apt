from database.db import db


class Categoria(db.Model):
    __tablename__ = 'categorias'

    id_categoria = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresas.id_empresa'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)

    empresa = db.relationship('Empresa', backref='categorias')

    def __repr__(self):
        return f'<Categoria {self.nombre}>'
