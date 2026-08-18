from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class EmpresaForm(FlaskForm):
    tipo_negocio = RadioField(
        'Que tipo de negocio tienes?',
        choices=[('pyme', 'PyME'), ('empresa', 'Empresa')],
        validators=[DataRequired(message='Debes seleccionar un tipo de negocio.')]
    )
    nombre_empresa = StringField(
        'Nombre del negocio',
        validators=[DataRequired(message='El nombre del negocio es obligatorio.'),
                    Length(max=150)]
    )
    rut = StringField(
        'RUT (opcional)',
        validators=[Optional(), Length(max=20)]
    )
    telefono = StringField(
        'Telefono de contacto (opcional)',
        validators=[Optional(), Length(max=20)]
    )
    direccion = StringField(
        'Direccion (opcional)',
        validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField('Guardar y continuar')
