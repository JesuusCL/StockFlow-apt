from flask import Flask, render_template, session
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from config import Config
from database.db import db

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializacion de extensiones
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesion para acceder a esta pagina.'
    # 'strong': si cambia la IP o el user-agent del navegador a mitad de la
    # sesion (señal de que la cookie pudo ser robada/copiada a otro equipo),
    # Flask-Login cierra la sesion automaticamente por seguridad.
    login_manager.session_protection = 'strong'

    @app.before_request
    def hacer_sesion_permanente():
        # Sin esto, PERMANENT_SESSION_LIFETIME (config.py) se ignora y la
        # sesion dura hasta que se cierre el navegador, sin expirar sola.
        session.permanent = True

    # Registro de Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.productos import productos_bp
    from routes.ventas import ventas_bp
    from routes.inventario import inventario_bp
    from routes.usuarios import usuarios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(productos_bp, url_prefix='/productos')
    app.register_blueprint(ventas_bp, url_prefix='/ventas')
    app.register_blueprint(inventario_bp, url_prefix='/inventario')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')

    # Paginas de error personalizadas: nunca se debe mostrar un stack trace
    # tecnico de Flask/SQLAlchemy al usuario final (regla del punto 23).
    @app.errorhandler(403)
    def error_403(_error):
        return render_template('errores/403.html'), 403

    @app.errorhandler(404)
    def error_404(_error):
        return render_template('errores/404.html'), 404

    @app.errorhandler(500)
    def error_500(_error):
        db.session.rollback()  # evita dejar la transaccion de BD a medias
        return render_template('errores/500.html'), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    from models.usuario import Usuario
    return db.session.get(Usuario, int(user_id))


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
