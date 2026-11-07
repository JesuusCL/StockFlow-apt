from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user

from services import inventario_service, producto_service, alertas_stock_service
from forms.inventario_forms import EntradaStockForm

inventario_bp = Blueprint('inventario', __name__)


def _empresa_id_o_redirect():
    if current_user.empresa is None:
        return None
    return current_user.empresa.id_empresa


@inventario_bp.route('/entrada', methods=['GET', 'POST'])
@login_required
def entrada():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    productos = producto_service.listar_productos(empresa_id).all()
    if not productos:
        flash('Primero debes crear al menos un producto antes de ingresar stock.', 'warning')
        return redirect(url_for('productos.crear'))

    form = EntradaStockForm()
    form.id_producto.choices = [
        (p.id_producto, f'{p.nombre} (stock actual: {p.stock_actual})') for p in productos
    ]

    if form.validate_on_submit():
        producto = producto_service.obtener_producto_de_empresa(form.id_producto.data, empresa_id)
        if producto is None:
            abort(404)

        inventario_service.registrar_entrada(
            producto, form.cantidad.data, current_user.id_usuario, form.motivo.data
        )
        flash(
            f'Se agregaron {form.cantidad.data} unidades a "{producto.nombre}". '
            f'Nuevo stock: {producto.stock_actual}.',
            'success'
        )
        return redirect(url_for('inventario.movimientos'))

    return render_template('inventario/entrada.html', form=form)


@inventario_bp.route('/movimientos')
@login_required
def movimientos():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    producto_id = request.args.get('producto', type=int)
    pagina = request.args.get('pagina', 1, type=int)

    query = inventario_service.listar_movimientos(empresa_id, producto_id)
    movimientos_paginados = query.paginate(page=pagina, per_page=15, error_out=False)

    productos = producto_service.listar_productos(empresa_id).all()

    return render_template(
        'inventario/movimientos.html',
        movimientos=movimientos_paginados,
        productos=productos,
        producto_id=producto_id,
    )


@inventario_bp.route('/alertas')
@login_required
def alertas():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    productos_bajo = producto_service.productos_con_stock_bajo(empresa_id)
    return render_template('inventario/alertas.html', productos=productos_bajo)


@inventario_bp.route('/alertas/estado')
@login_required
def alertas_estado():
    """
    Lo consulta el aviso de "Stock bajo" de la pagina (JavaScript, cada 5 minutos).
    Devuelve cuantos productos estan bajo el minimo y, ademas, dispara el correo
    de alerta (maximo 1 por hora por empresa, ver config.py).
    """
    empresa = current_user.empresa
    if empresa is None:
        return jsonify(count=0, productos=[])

    productos_bajo = producto_service.productos_con_stock_bajo(empresa.id_empresa)
    alertas_stock_service.notificar_por_correo_si_corresponde(current_user, empresa, productos_bajo)

    respuesta = jsonify(
        count=len(productos_bajo),
        productos=[
            {'nombre': p.nombre, 'stock_actual': p.stock_actual, 'stock_minimo': p.stock_minimo}
            for p in productos_bajo[:5]
        ],
        url_alertas=url_for('inventario.alertas'),
    )
    respuesta.headers['Cache-Control'] = 'no-store'
    return respuesta
