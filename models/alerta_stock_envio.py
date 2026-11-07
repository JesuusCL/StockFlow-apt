from database.db import db


class AlertaStockEnvio(db.Model):
    """Registra cuando se envio por ultima vez el correo de stock bajo de una empresa."""
    __tablename__ = 'alertas_stock_envio'

    id_empresa = db.Column(db.Integer, db.ForeignKey('empresas.id_empresa'), primary_key=True)
    ultimo_envio = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<AlertaStockEnvio empresa={self.id_empresa} ultimo={self.ultimo_envio}>'
