from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Length


class EntradaStockForm(FlaskForm):
    id_producto = SelectField(
        'Producto',
        coerce=int,
        validators=[DataRequired(message='Selecciona un producto.')]
    )
    cantidad = IntegerField(
        'Cantidad a ingresar',
        validators=[DataRequired(message='Ingresa una cantidad.'),
                    NumberRange(min=1, message='La cantidad debe ser al menos 1.')]
    )
    motivo = StringField(
        'Motivo (opcional)',
        validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField('Registrar entrada')
