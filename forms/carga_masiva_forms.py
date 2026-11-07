from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField


class CargaMasivaForm(FlaskForm):
    archivo = FileField(
        'Archivo CSV o Excel',
        validators=[
            FileRequired(message='Debes seleccionar un archivo.'),
            FileAllowed(['csv', 'xlsx'], message='Solo se permiten archivos .csv o .xlsx.'),
        ]
    )
    submit = SubmitField('Cargar productos')
