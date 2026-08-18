from flask_sqlalchemy import SQLAlchemy

# Instancia unica de SQLAlchemy. Se inicializa con la app en app.py (db.init_app(app))
# y se importa desde cada modelo en models/ para heredar de db.Model.
db = SQLAlchemy()
