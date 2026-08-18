from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from services import dashboard_service, producto_service

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    if current_user.empresa is None:
        return redirect(url_for('usuarios.configuracion_empresa'))

    empresa_id = current_user.empresa.id_empresa

    resumen = dashboard_service.obtener_resumen(empresa_id)
    etiquetas_ventas, valores_ventas = dashboard_service.ventas_ultimos_dias(empresa_id)
    productos_bajo = producto_service.productos_con_stock_bajo(empresa_id)

    return render_template(
        'dashboard.html',
        resumen=resumen,
        etiquetas_ventas=etiquetas_ventas,
        valores_ventas=valores_ventas,
        productos_bajo=productos_bajo,
    )
