from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError

from models.producto import Producto


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
    id_categoria = SelectField(
        'Categoria (opcional)',
        coerce=int,
        validators=[Optional()]
    )
    precio_compra = DecimalField(
        'Precio de compra',
        validators=[DataRequired(message='El precio de compra es obligatorio.'),
                    NumberRange(min=0, message='No puede ser negativo.')],
        places=2
    )
    precio_venta = DecimalField(
        'Precio de venta',
        validators=[DataRequired(message='El precio de venta es obligatorio.'),
                    NumberRange(min=0, message='No puede ser negativo.')],
        places=2
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
