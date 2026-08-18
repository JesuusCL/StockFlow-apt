import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from database.db import db
from models.usuario import Usuario
from forms.auth_forms import RegistroForm, LoginForm, SolicitarResetForm, RestablecerPasswordForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistroForm()

    if form.validate_on_submit():
        nuevo_usuario = Usuario(
            nombre_usuario=form.nombre_usuario.data,
            correo=form.correo.data,
            nombre_completo=form.nombre_completo.data,
        )
        nuevo_usuario.set_password(form.password.data)

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Ocurrio un error al crear tu cuenta. Intenta nuevamente.', 'danger')
            return render_template('registro.html', form=form)

        login_user(nuevo_usuario)
        flash('Cuenta creada correctamente. Ahora configuremos tu empresa.', 'success')
        return redirect(url_for('usuarios.configuracion_empresa'))

    return render_template('registro.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()

    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(correo=form.correo.data).first()

        if usuario is not None and usuario.check_password(form.password.data):
            login_user(usuario)
            siguiente = request.args.get('next')
            return redirect(siguiente or url_for('dashboard.index'))

        # Mensaje generico a proposito: no revelamos si fallo el correo o la
        # contrasena, para no facilitar ataques de enumeracion de usuarios.
        flash('Correo o contrasena incorrectos.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesion cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/recuperar-password', methods=['GET', 'POST'])
def recuperar_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = SolicitarResetForm()
    enlace_generado = None

    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(correo=form.correo.data).first()

        # Por seguridad, el mensaje es igual exista o no el correo
        # (evita que alguien pueda usar este formulario para "descubrir"
        # que correos estan registrados en el sistema).
        if usuario is not None:
            usuario.reset_token = secrets.token_urlsafe(32)
            usuario.reset_token_expira = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            enlace_generado = url_for(
                'auth.restablecer_password', token=usuario.reset_token, _external=True
            )
            # En produccion, aqui se enviaria enlace_generado por correo
            # (ej. con Flask-Mail) en vez de mostrarlo en pantalla.

        flash('Si el correo esta registrado, se genero un enlace de recuperacion.', 'success')

    return render_template('recuperar_password.html', form=form, enlace_generado=enlace_generado)


@auth_bp.route('/restablecer-password/<token>', methods=['GET', 'POST'])
def restablecer_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    usuario = Usuario.query.filter_by(reset_token=token).first()

    if usuario is None or usuario.reset_token_expira is None or usuario.reset_token_expira < datetime.utcnow():
        flash('El enlace de recuperacion no es valido o ya expiro. Solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.recuperar_password'))

    form = RestablecerPasswordForm()

    if form.validate_on_submit():
        usuario.set_password(form.password.data)
        usuario.reset_token = None
        usuario.reset_token_expira = None
        db.session.commit()

        flash('Tu contrasena fue actualizada. Ya puedes iniciar sesion.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('restablecer_password.html', form=form)
