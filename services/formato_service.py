from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def formato_clp(valor):
    """
    Formatea un monto en pesos chilenos: sin decimales y con punto como
    separador de miles. Ejemplos: 30000 -> $30.000 ; Decimal('15000.00') -> $15.000
    Se usa en las plantillas como:  {{ producto.precio_venta | clp }}
    """
    if valor is None or valor == '':
        return '$0'
    try:
        numero = Decimal(str(valor))
    except InvalidOperation:
        return '$0'

    entero = int(numero.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    signo = '-' if entero < 0 else ''
    return f'{signo}${abs(entero):,}'.replace(',', '.')
