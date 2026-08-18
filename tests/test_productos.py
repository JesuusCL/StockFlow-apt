from models.producto import Producto


def _crear_producto(cliente, **overrides):
    datos = {
        'nombre': 'Producto Test',
        'descripcion': '',
        'sku': 'SKU-001',
        'id_categoria': 0,
        'precio_compra': '1000',
        'precio_venta': '1500',
        'stock_minimo': '5',
    }
    datos.update(overrides)
    return cliente.post('/productos/nuevo', data=datos, follow_redirects=True)


def test_crear_producto_exitoso(cliente_logueado, app):
    _crear_producto(cliente_logueado)

    with app.app_context():
        assert Producto.query.filter_by(sku='SKU-001').count() == 1


def test_producto_nuevo_empieza_con_stock_cero(cliente_logueado, app):
    _crear_producto(cliente_logueado)

    with app.app_context():
        producto = Producto.query.filter_by(sku='SKU-001').first()
        assert producto.stock_actual == 0


def test_rechaza_sku_duplicado_en_la_misma_empresa(cliente_logueado):
    _crear_producto(cliente_logueado)
    respuesta = _crear_producto(cliente_logueado, nombre='Otro producto')

    assert 'Ya existe un producto con ese SKU'.encode('utf-8') in respuesta.data


def test_rechaza_precio_venta_menor_a_precio_compra(cliente_logueado):
    respuesta = _crear_producto(cliente_logueado, precio_compra='2000', precio_venta='1000')

    assert 'no puede ser menor'.encode('utf-8') in respuesta.data


def test_empresa_no_puede_acceder_a_producto_de_otra_empresa(client, app, usuario_empresa):
    """
    Esta es la prueba mas importante de todo el sistema: confirma la regla
    de negocio del punto 5/21 del documento de requisitos (aislamiento total
    de datos entre empresas). Simula un intento de acceso indebido (IDOR).
    """
    # 1. El usuario A crea un producto en su empresa
    client.post('/login', data={
        'correo': usuario_empresa['correo'], 'password': usuario_empresa['password'],
    }, follow_redirects=True)
    _crear_producto(client)

    with app.app_context():
        producto_de_empresa_a = Producto.query.filter_by(sku='SKU-001').first()
        id_producto_ajeno = producto_de_empresa_a.id_producto

    client.get('/logout', follow_redirects=True)

    # 2. Un usuario B, de OTRA empresa, intenta editar ese producto por URL
    client.post('/registro', data={
        'nombre_completo': 'Usuario B', 'nombre_usuario': 'usuariob',
        'correo': 'usuariob@test.com', 'password': 'Password123',
        'confirmar_password': 'Password123',
    }, follow_redirects=True)
    client.post('/usuarios/configuracion-empresa', data={
        'tipo_negocio': 'empresa', 'nombre_empresa': 'Empresa B',
    }, follow_redirects=True)

    respuesta = client.get(f'/productos/{id_producto_ajeno}/editar')

    # Debe dar 404 (no revelar que el producto existe en otra empresa)
    assert respuesta.status_code == 404
