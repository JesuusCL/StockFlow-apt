from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from models.usuario import Usuario


class RegistroForm(FlaskForm):
    nombre_completo = StringField(
        'Nombre completo',
        validators=[DataRequired(message='El nombre completo es obligatorio.'),
                    Length(max=150)]
    )
    nombre_usuario = StringField(
        'Nombre de usuario',
        validators=[DataRequired(message='El nombre de usuario es obligatorio.'),
                    Length(min=3, max=50, message='Debe tener entre 3 y 50 caracteres.')]
    )
    correo = StringField(
        'Correo electronico',
        validators=[DataRequired(message='El correo es obligatorio.'),
                    Email(message='Ingresa un correo valido.')]
    )
    password = PasswordField(
        'Contrasena',
        validators=[DataRequired(message='La contrasena es obligatoria.'),
                    Length(min=8, message='Debe tener al menos 8 caracteres.')]
    )
    confirmar_password = PasswordField(
        'Confirmar contrasena',
        validators=[DataRequired(message='Debes confirmar la contrasena.'),
                    EqualTo('password', message='Las contrasenas no coinciden.')]
    )
    submit = SubmitField('Crear cuenta')

    def validate_nombre_usuario(self, field):
        """Validador custom de WTForms: se ejecuta automaticamente al llamar validate_on_submit()."""
        if Usuario.query.filter_by(nombre_usuario=field.data).first():
            raise ValidationError('Ese nombre de usuario ya esta en uso.')

    def validate_correo(self, field):
        if Usuario.query.filter_by(correo=field.data).first():
            raise ValidationError('Ese correo electronico ya esta registrado.')


class LoginForm(FlaskForm):
    correo = StringField(
        'Correo electronico',
        validators=[DataRequired(message='El correo es obligatorio.'),
                    Email(message='Ingresa un correo valido.')]
    )
    password = PasswordField(
        'Contrasena',
        validators=[DataRequired(message='La contrasena es obligatoria.')]
    )
    submit = SubmitField('Iniciar sesion')


class SolicitarResetForm(FlaskForm):
    correo = StringField(
        'Correo electronico',
        validators=[DataRequired(message='El correo es obligatorio.'),
                    Email(message='Ingresa un correo valido.')]
    )
    submit = SubmitField('Enviar enlace de recuperacion')


class RestablecerPasswordForm(FlaskForm):
    password = PasswordField(
        'Nueva contrasena',
        validators=[DataRequired(message='La contrasena es obligatoria.'),
                    Length(min=8, message='Debe tener al menos 8 caracteres.')]
    )
    confirmar_password = PasswordField(
        'Confirmar nueva contrasena',
        validators=[DataRequired(message='Debes confirmar la contrasena.'),
                    EqualTo('password', message='Las contrasenas no coinciden.')]
    )
    submit = SubmitField('Restablecer contrasena')
