from flask_wtf import FlaskForm


class VentaForm(FlaskForm):
    """
    Formulario intencionalmente vacio de campos fijos: una venta tiene un
    numero variable de productos, que se agregan dinamicamente en el HTML.
    FlaskForm igual nos da hidden_tag() con el token CSRF automaticamente.
    """
    pass
