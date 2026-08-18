from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import db


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expira = db.Column(db.DateTime, nullable=True)

    # La relacion con Empresa (1 a 1) se agrega en la Fase 5,
    # cuando se cree el modelo models/empresa.py

    def set_password(self, password):
        """Genera y guarda el hash de la contrasena. Nunca se guarda en texto plano."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Compara una contrasena en texto plano contra el hash guardado."""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Flask-Login requiere que get_id() devuelva un string
        return str(self.id_usuario)

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'
