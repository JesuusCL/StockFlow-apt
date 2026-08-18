from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from services import ventas_service, producto_service
from forms.venta_forms import VentaForm

ventas_bp = Blueprint('ventas', __name__)


def _empresa_id_o_redirect():
    if current_user.empresa is None:
        return None
    return current_user.empresa.id_empresa


@ventas_bp.route('/')
@login_required
def listar():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    rango = request.args.get('rango', 'todos')
    desde = request.args.get('desde', '')
    hasta = request.args.get('hasta', '')
    pagina = request.args.get('pagina', 1, type=int)

    query = ventas_service.listar_ventas(empresa_id, rango, desde, hasta)
    ventas_paginadas = query.paginate(page=pagina, per_page=10, error_out=False)

    return render_template(
        'ventas/listar.html',
        ventas=ventas_paginadas, rango=rango, desde=desde, hasta=hasta,
    )


@ventas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    productos = producto_service.listar_productos(empresa_id).all()
    if not productos:
        flash('Primero debes crear productos antes de registrar una venta.', 'warning')
        return redirect(url_for('productos.crear'))

    form = VentaForm()

    if request.method == 'POST' and form.validate_on_submit():
        producto_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')

        items = []
        for pid, cant in zip(producto_ids, cantidades):
            if pid and cant:
                try:
                    items.append({'producto_id': int(pid), 'cantidad': int(cant)})
                except ValueError:
                    flash('Los datos de la venta no son validos.', 'danger')
                    return render_template('ventas/nueva.html', form=form, productos=productos)

        try:
            venta = ventas_service.registrar_venta(empresa_id, current_user.id_usuario, items)
        except ValueError as error:
            flash(str(error), 'danger')
            return render_template('ventas/nueva.html', form=form, productos=productos)

        flash(f'Venta #{venta.id_venta} registrada correctamente. Total: ${venta.total:.2f}', 'success')
        return redirect(url_for('ventas.detalle', venta_id=venta.id_venta))

    return render_template('ventas/nueva.html', form=form, productos=productos)


@ventas_bp.route('/<int:venta_id>')
@login_required
def detalle(venta_id):
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    venta = ventas_service.obtener_venta_de_empresa(venta_id, empresa_id)
    if venta is None:
        abort(404)

    return render_template('ventas/detalle.html', venta=venta)
