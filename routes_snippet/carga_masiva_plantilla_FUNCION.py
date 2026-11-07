"""
NO reemplaces todo tu routes/productos.py con este archivo.

Este archivo contiene SOLO la funcion carga_masiva_plantilla() actualizada.
Abre tu routes/productos.py real, busca la funcion que ya tienes con ese
mismo nombre (@productos_bp.route('/carga-masiva/plantilla')) y reemplaza
SOLO esa funcion completa por la que esta abajo.

Antes de pegarla, agrega estos imports al inicio de routes/productos.py
(si no los tienes ya):

    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

No olvides instalar la libreria si aun no la tienes:
    pip install openpyxl
    (y agregar la linea openpyxl==3.1.5 a requirements.txt)
"""

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
