from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from database.db import db
from models.empresa import Empresa
from forms.empresa_forms import EmpresaForm

usuarios_bp = Blueprint('usuarios', __name__)


@usuarios_bp.route('/configuracion-empresa', methods=['GET', 'POST'])
@login_required
def configuracion_empresa():
    # Si el usuario ya configuro su empresa, no debe volver a pasar por aqui
    if current_user.empresa is not None:
        return redirect(url_for('dashboard.index'))

    form = EmpresaForm()

    if form.validate_on_submit():
        nueva_empresa = Empresa(
            id_usuario=current_user.id_usuario,
            nombre_empresa=form.nombre_empresa.data,
            tipo_negocio=form.tipo_negocio.data,
            rut=form.rut.data or None,
            telefono=form.telefono.data or None,
            direccion=form.direccion.data or None,
        )

        try:
            db.session.add(nueva_empresa)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Ocurrio un error al guardar la informacion de tu empresa. Intenta nuevamente.', 'danger')
            return render_template('configuracion_empresa.html', form=form)

        flash('Empresa configurada correctamente.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('configuracion_empresa.html', form=form)


@usuarios_bp.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')
