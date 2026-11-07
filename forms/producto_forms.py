from decimal import Decimal, InvalidOperation

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError

from models.producto import Producto

EXTENSIONES_IMAGEN_PERMITIDAS = ['jpg', 'jpeg', 'png', 'webp']


class PrecioField(DecimalField):
    """
    Campo de precio en pesos chilenos. Acepta el formato con que se escribe en
    Chile: el punto separa los miles ("30.000" = treinta mil) y la coma, si se
    usa, separa decimales ("30,5"). Tambien acepta "30000" y "$30.000".
    Sin esto, "30.000" se leia como 30 (punto decimal) y el precio quedaba mal.
    """

    def process_formdata(self, valuelist):
        if not valuelist:
            return
        texto = valuelist[0].strip().replace('$', '').replace(' ', '')
        texto = texto.replace('.', '').replace(',', '.')
        try:
            self.data = Decimal(texto)
        except (InvalidOperation, ValueError):
            self.data = None
            raise ValueError(self.gettext('Ingresa un precio valido (ejemplo: 30.000).'))

    def _value(self):
        # Al editar, el valor se muestra sin ".00": 30000 (no 30000.00), para que
        # al guardar de nuevo no se vuelva a interpretar mal.
        if self.raw_data:
            return self.raw_data[0]
        if self.data is None:
            return ''
        entero = self.data.to_integral_value()
        if self.data == entero:
            return str(int(entero))
        return str(self.data).replace('.', ',')


class ProductoForm(FlaskForm):
    nombre = StringField(
        'Nombre del producto',
        validators=[DataRequired(message='El nombre es obligatorio.'), Length(max=150)]
    )
    descripcion = TextAreaField(
        'Descripcion (opcional)',
        validators=[Optional()]
    )
    sku = StringField(
        'SKU / Codigo',
        validators=[DataRequired(message='El SKU es obligatorio.'), Length(max=50)]
    )
    imagen = FileField(
        'Foto del producto (opcional)',
        validators=[
            FileAllowed(
                EXTENSIONES_IMAGEN_PERMITIDAS,
                'Solo se permiten imagenes (jpg, png o webp).'
            )
        ]
    )
    id_categoria = SelectField(
        'Categoria (opcional)',
        coerce=int,
        validators=[Optional()]
    )
    precio_compra = PrecioField(
        'Precio de compra',
        validators=[DataRequired(message='El precio de compra es obligatorio.'),
                    NumberRange(min=0, message='No puede ser negativo.')]
    )
    precio_venta = PrecioField(
        'Precio de venta',
        validators=[DataRequired(message='El precio de venta es obligatorio.'),
                    NumberRange(min=0, message='No puede ser negativo.')]
    )
    stock_minimo = IntegerField(
        'Stock minimo (alerta de stock bajo)',
        default=5,
        validators=[DataRequired(), NumberRange(min=0, message='No puede ser negativo.')]
    )
    submit = SubmitField('Guardar producto')

    def __init__(self, empresa_id, producto_id_actual=None, *args, **kwargs):
        """
        empresa_id: la empresa del usuario autenticado, para validar SKU unico
                    solo dentro de esa empresa (no globalmente).
        producto_id_actual: al editar, excluye el propio producto de la
                    validacion de duplicado (si no, siempre chocaria consigo mismo).
        """
        super().__init__(*args, **kwargs)
        self.empresa_id = empresa_id
        self.producto_id_actual = producto_id_actual

    def validate_sku(self, field):
        consulta = Producto.query.filter_by(id_empresa=self.empresa_id, sku=field.data)
        if self.producto_id_actual:
            consulta = consulta.filter(Producto.id_producto != self.producto_id_actual)
        if consulta.first():
            raise ValidationError('Ya existe un producto con ese SKU en tu empresa.')

    def validate_precio_venta(self, field):
        if self.precio_compra.data is not None and field.data is not None:
            if field.data < self.precio_compra.data:
                raise ValidationError('El precio de venta no puede ser menor al precio de compra.')
