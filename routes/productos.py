from io import BytesIO

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from services import producto_service, categoria_service, carga_masiva_service
from forms.producto_forms import ProductoForm
from forms.categoria_forms import CategoriaForm
from forms.carga_masiva_forms import CargaMasivaForm
from models.carga_masiva import CargaMasiva

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
        imagen_guardada = producto_service.guardar_imagen_producto(form.imagen.data)
        producto_service.crear_producto(empresa_id, {
            'nombre': form.nombre.data,
            'descripcion': form.descripcion.data,
            'sku': form.sku.data,
            'imagen': imagen_guardada,
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
        abort(404)

    form = ProductoForm(empresa_id=empresa_id, producto_id_actual=producto.id_producto, obj=producto)
    form.id_categoria.choices = [(0, 'Sin categoria')] + [
        (c.id_categoria, c.nombre) for c in categoria_service.listar_categorias(empresa_id)
    ]
    if request.method == 'GET':
        form.id_categoria.data = producto.id_categoria or 0

    if form.validate_on_submit():
        imagen_guardada = producto_service.guardar_imagen_producto(form.imagen.data)
        producto_service.actualizar_producto(producto, {
            'nombre': form.nombre.data,
            'descripcion': form.descripcion.data,
            'sku': form.sku.data,
            'imagen': imagen_guardada,
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


# ============================================================
# Carga masiva de productos (CSV / Excel)
# ============================================================

@productos_bp.route('/carga-masiva', methods=['GET', 'POST'])
@login_required
def carga_masiva():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    form = CargaMasivaForm()

    if form.validate_on_submit():
        archivo = form.archivo.data
        try:
            carga = carga_masiva_service.procesar_carga(empresa_id, current_user.id_usuario, archivo)
        except ValueError as error:
            flash(str(error), 'danger')
            return render_template('productos/carga_masiva.html', form=form)

        if carga.filas_con_error == 0:
            flash(f'Carga exitosa: se crearon {carga.filas_exitosas} de {carga.total_filas} productos.', 'success')
        else:
            flash(
                f'Carga procesada con observaciones: {carga.filas_exitosas} de {carga.total_filas} '
                f'productos creados. Revisa el detalle de las filas con error mas abajo.',
                'warning'
            )
        return redirect(url_for('productos.carga_masiva_detalle', carga_id=carga.id_carga))

    return render_template('productos/carga_masiva.html', form=form)


@productos_bp.route('/carga-masiva/plantilla')
@login_required
def carga_masiva_plantilla():
    """Genera y descarga la plantilla Excel para carga masiva de productos."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Carga masiva"

    headers = [
        "nombre", "sku", "categoria", "descripcion",
        "precio_compra", "precio_venta", "stock_inicial", "stock_minimo",
        "ganancia_obtenida",
    ]
    ws.append(headers)

    header_fill = PatternFill(start_color="16233E", end_color="16233E", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    thin = Side(style="thin", color="B0B0B0")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"

    ejemplos = [
        ["Polera deportiva", "POL-001", "Ropa deportiva", "Polera de secado rapido, talla unica", 8000, 15000, 20, 5],
        ["Short deportivo", "SHO-001", "Ropa deportiva", "Short liviano para entrenamiento", 6000, 12000, 15, 5],
    ]

    for i, fila in enumerate(ejemplos, start=2):
        for col, valor in enumerate(fila, start=1):
            cell = ws.cell(row=i, column=col, value=valor)
            cell.border = border
            if col in (5, 6):
                cell.number_format = '"$"#,##0'
        ganancia_cell = ws.cell(row=i, column=9, value=f"=F{i}-E{i}")
        ganancia_cell.number_format = '"$"#,##0'
        ganancia_cell.border = border
        ganancia_cell.font = Font(italic=True, color="2F5FE0")

    for col in range(1, 9):
        ws.cell(row=4, column=col).border = border
    ws.cell(row=4, column=9, value="=F4-E4").border = border
    ws.cell(row=4, column=9).number_format = '"$"#,##0'
    ws.cell(row=4, column=9).font = Font(italic=True, color="2F5FE0")

    anchos = {"A": 22, "B": 12, "C": 18, "D": 34, "E": 14, "F": 14, "G": 14, "H": 14, "I": 16}
    for col, width in anchos.items():
        ws.column_dimensions[col].width = width

    ws2 = wb.create_sheet("Instrucciones")
    ws2.column_dimensions["A"].width = 100
    instrucciones = [
        "INSTRUCCIONES - Plantilla de carga masiva de productos (StockFlow)",
        "",
        "1. No cambies el nombre de las columnas de la hoja 'Carga masiva' (nombre, sku, categoria, descripcion, "
        "precio_compra, precio_venta, stock_inicial, stock_minimo). El sistema las identifica por ese nombre exacto.",
        "2. 'nombre' y 'sku' son obligatorios. El SKU debe ser unico dentro de tu empresa.",
        "3. 'categoria' es opcional. Si escribes una categoria que no existe, el sistema la crea automaticamente.",
        "4. 'descripcion' es opcional.",
        "5. 'stock_inicial' y 'stock_minimo' son opcionales (si se dejan vacios, se usa 0 y 5 respectivamente).",
        "6. El precio de venta no puede ser menor al precio de compra.",
        "7. La columna 'ganancia_obtenida' es solo referencial (formula de Excel). El sistema la ignora al subir el archivo.",
        "8. Borra las filas de ejemplo antes de cargar tus propios productos.",
        "9. Formatos aceptados para subir: .csv o .xlsx",
    ]
    for i, linea in enumerate(instrucciones, start=1):
        cell = ws2.cell(row=i, column=1, value=linea)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if i == 1:
            cell.font = Font(bold=True, size=13, color="16233E")

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_carga_masiva.xlsx"},
    )


@productos_bp.route('/carga-masiva/historial')
@login_required
def carga_masiva_historial():
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    cargas = (CargaMasiva.query
              .filter_by(id_empresa=empresa_id)
              .order_by(CargaMasiva.fecha_carga.desc())
              .all())
    return render_template('productos/carga_masiva_historial.html', cargas=cargas)


@productos_bp.route('/carga-masiva/<int:carga_id>')
@login_required
def carga_masiva_detalle(carga_id):
    empresa_id = _empresa_id_o_redirect()
    if empresa_id is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    carga = CargaMasiva.query.filter_by(id_carga=carga_id, id_empresa=empresa_id).first()
    if carga is None:
        abort(404)

    return render_template('productos/carga_masiva_resultado.html', carga=carga)
