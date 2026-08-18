from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CategoriaForm(FlaskForm):
    nombre = StringField(
        'Nombre de la categoria',
        validators=[DataRequired(message='El nombre es obligatorio.'), Length(max=100)]
    )
    descripcion = StringField(
        'Descripcion (opcional)',
        validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField('Crear categoria')
