from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from services import producto_service, categoria_service
from forms.producto_forms import ProductoForm
from forms.categoria_forms import CategoriaForm

productos_bp = Blueprint('productos', __name__)


def _empresa_id_o_redirect():
    """Todas las rutas de este modulo requieren que el usuario ya tenga
    empresa configurada. Si no la tiene, no hay id_empresa por el cual filtrar."""
    if current_user.empresa is None:
        return None
    return current_user.empresa.id_empresa


@productos_bp.route('/')
@login_required
def listar():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    busqueda = request.args.get('q', '').strip()
    categoria_id = request.args.get('categoria', type=int)
    orden = request.args.get('orden', 'nombre')
    pagina = request.args.get('pagina', 1, type=int)

    query = producto_service.listar_productos(empresa_id, busqueda, categoria_id, orden)
    productos_paginados = query.paginate(page=pagina, per_page=10, error_out=False)

    categorias = categoria_service.listar_categorias(empresa_id)

    return render_template(
        'productos/listar.html',
        productos=productos_paginados,
        categorias=categorias,
        busqueda=busqueda,
        categoria_id=categoria_id,
        orden=orden,
    )


@productos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def crear():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    form = ProductoForm(empresa_id=empresa_id)
    form.id_categoria.choices = [(0, 'Sin categoria')] + [
        (c.id_categoria, c.nombre) for c in categoria_service.listar_categorias(empresa_id)
    ]

    if form.validate_on_submit():
        producto_service.crear_producto(empresa_id, {
            'nombre': form.nombre.data,
            'descripcion': form.descripcion.data,
            'sku': form.sku.data,
            'id_categoria': form.id_categoria.data if form.id_categoria.data != 0 else None,
            'precio_compra': form.precio_compra.data,
            'precio_venta': form.precio_venta.data,
            'stock_minimo': form.stock_minimo.data,
        })
        flash('Producto creado correctamente. El stock inicial es 0; usa "Entrada de stock" para ingresarlo.', 'success')
        return redirect(url_for('productos.listar'))

    return render_template('productos/formulario.html', form=form, modo='crear')


@productos_bp.route('/<int:producto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(producto_id):
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    producto = producto_service.obtener_producto_de_empresa(producto_id, empresa_id)
    if producto is None:
        # No revelamos si el producto existe en OTRA empresa: simplemente 404.
        abort(404)

    form = ProductoForm(empresa_id=empresa_id, producto_id_actual=producto.id_producto, obj=producto)
    form.id_categoria.choices = [(0, 'Sin categoria')] + [
        (c.id_categoria, c.nombre) for c in categoria_service.listar_categorias(empresa_id)
    ]
    if request.method == 'GET':
        form.id_categoria.data = producto.id_categoria or 0

    if form.validate_on_submit():
        producto_service.actualizar_producto(producto, {
            'nombre': form.nombre.data,
            'descripcion': form.descripcion.data,
            'sku': form.sku.data,
            'id_categoria': form.id_categoria.data if form.id_categoria.data != 0 else None,
            'precio_compra': form.precio_compra.data,
            'precio_venta': form.precio_venta.data,
            'stock_minimo': form.stock_minimo.data,
        })
        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('productos.listar'))

    return render_template('productos/formulario.html', form=form, modo='editar', producto=producto)


@productos_bp.route('/<int:producto_id>/eliminar', methods=['POST'])
@login_required
def eliminar(producto_id):
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    producto = producto_service.obtener_producto_de_empresa(producto_id, empresa_id)
    if producto is None:
        abort(404)

    producto_service.eliminar_producto(producto)
    flash(f'Producto "{producto.nombre}" eliminado correctamente.', 'info')
    return redirect(url_for('productos.listar'))


@productos_bp.route('/categorias', methods=['GET', 'POST'])
@login_required
def categorias():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    form = CategoriaForm()
    if form.validate_on_submit():
        categoria_service.crear_categoria(empresa_id, form.nombre.data, form.descripcion.data)
        flash('Categoria creada correctamente.', 'success')
        return redirect(url_for('productos.categorias'))

    lista_categorias = categoria_service.listar_categorias(empresa_id)
    return render_template('productos/categorias.html', form=form, categorias=lista_categorias)


@productos_bp.route('/categorias/<int:categoria_id>/eliminar', methods=['POST'])
@login_required
def eliminar_categoria(categoria_id):
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    categoria = categoria_service.obtener_categoria_de_empresa(categoria_id, empresa_id)
    if categoria is None:
        abort(404)

    categoria_service.eliminar_categoria(categoria)
    flash('Categoria eliminada. Los productos que la usaban quedaron sin categoria.', 'info')
    return redirect(url_for('productos.categorias'))
