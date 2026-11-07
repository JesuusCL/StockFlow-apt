import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user

from database.db import db
from models.usuario import Usuario
from forms.auth_forms import (RegistroForm, LoginForm, SolicitarResetForm,
                              RestablecerPasswordForm, CodigoVerificacionForm)
from services import autenticacion_service

auth_bp = Blueprint('auth', __name__)

# Claves de sesion usadas mientras el usuario esta a mitad del login (ya puso
# bien la contrasena pero aun no ingresa el codigo del correo).
SESION_2FA_USUARIO = '2fa_usuario_id'
SESION_2FA_SIGUIENTE = '2fa_siguiente'


def _url_segura(destino):
    """Solo se acepta redirigir a rutas internas del sitio (evita redirecciones a paginas externas)."""
    return bool(destino) and destino.startswith('/') and not destino.startswith('//')


def _usuario_pendiente_2fa():
    id_usuario = session.get(SESION_2FA_USUARIO)
    if id_usuario is None:
        return None
    return db.session.get(Usuario, id_usuario)


def _limpiar_sesion_2fa():
    session.pop(SESION_2FA_USUARIO, None)
    session.pop(SESION_2FA_SIGUIENTE, None)


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
            siguiente = request.args.get('next')

            if not current_app.config.get('LOGIN_2FA_ENABLED', True):
                login_user(usuario)
                return redirect(siguiente if _url_segura(siguiente) else url_for('dashboard.index'))

            # Segundo paso: contrasena correcta, ahora falta el codigo del correo.
            if not autenticacion_service.generar_y_enviar_codigo(usuario):
                flash('No pudimos enviar el codigo a tu correo. Intenta nuevamente en unos minutos.', 'danger')
                return render_template('login.html', form=form)

            session[SESION_2FA_USUARIO] = usuario.id_usuario
            session[SESION_2FA_SIGUIENTE] = siguiente if _url_segura(siguiente) else None
            flash('Te enviamos un codigo de verificacion a tu correo.', 'info')
            return redirect(url_for('auth.verificar_codigo'))

        # Mensaje generico a proposito: no revelamos si fallo el correo o la
        # contrasena, para no facilitar ataques de enumeracion de usuarios.
        flash('Correo o contrasena incorrectos.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/verificar-codigo', methods=['GET', 'POST'])
def verificar_codigo():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    usuario = _usuario_pendiente_2fa()
    if usuario is None:
        flash('Tu verificacion expiro. Inicia sesion nuevamente.', 'warning')
        return redirect(url_for('auth.login'))

    form = CodigoVerificacionForm()

    if form.validate_on_submit():
        ok, motivo, restantes = autenticacion_service.verificar_codigo(usuario, form.codigo.data)

        if ok:
            siguiente = session.get(SESION_2FA_SIGUIENTE)
            _limpiar_sesion_2fa()
            login_user(usuario)
            return redirect(siguiente if _url_segura(siguiente) else url_for('dashboard.index'))

        if motivo == 'incorrecto':
            flash(f'Codigo incorrecto. Te quedan {restantes} intento(s).', 'danger')
        elif motivo == 'bloqueado':
            flash('Superaste los intentos permitidos. Solicita un codigo nuevo.', 'danger')
        else:  # expirado o sin_codigo
            flash('El codigo vencio. Solicita uno nuevo.', 'warning')

    return render_template(
        'verificar_codigo.html',
        form=form,
        correo_enmascarado=autenticacion_service.enmascarar_correo(usuario.correo),
        segundos_reenvio=autenticacion_service.segundos_para_reenvio(usuario),
        minutos_vigencia=current_app.config['CODIGO_2FA_MINUTOS'],
    )


@auth_bp.route('/reenviar-codigo', methods=['POST'])
def reenviar_codigo():
    usuario = _usuario_pendiente_2fa()
    if usuario is None:
        flash('Tu verificacion expiro. Inicia sesion nuevamente.', 'warning')
        return redirect(url_for('auth.login'))

    espera = autenticacion_service.segundos_para_reenvio(usuario)
    if espera > 0:
        flash(f'Espera {espera} segundos antes de pedir otro codigo.', 'warning')
    elif autenticacion_service.generar_y_enviar_codigo(usuario):
        flash('Te enviamos un codigo nuevo a tu correo.', 'success')
    else:
        flash('No pudimos enviar el codigo. Intenta nuevamente en unos minutos.', 'danger')

    return redirect(url_for('auth.verificar_codigo'))


@auth_bp.route('/cancelar-verificacion')
def cancelar_verificacion():
    _limpiar_sesion_2fa()
    return redirect(url_for('auth.login'))


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
