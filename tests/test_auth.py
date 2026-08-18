from models.usuario import Usuario


# --- Prueba unitaria: no depende de la base de datos ni de rutas HTTP ---

def test_password_nunca_se_guarda_en_texto_plano(app):
    with app.app_context():
        usuario = Usuario(nombre_usuario='x', correo='x@test.com', nombre_completo='X')
        usuario.set_password('miclaveSegura123')

        assert usuario.password_hash != 'miclaveSegura123'
        assert usuario.check_password('miclaveSegura123') is True
        assert usuario.check_password('claveIncorrecta') is False


# --- Pruebas funcionales: simulan peticiones HTTP reales ---

def test_registro_exitoso_crea_usuario_y_redirige_a_configurar_empresa(client, app):
    respuesta = client.post('/registro', data={
        'nombre_completo': 'Juan Perez',
        'nombre_usuario': 'juanperez',
        'correo': 'juan@test.com',
        'password': 'Password123',
        'confirmar_password': 'Password123',
    }, follow_redirects=True)

    assert respuesta.status_code == 200
    assert 'Configura tu espacio de trabajo'.encode('utf-8') in respuesta.data

    with app.app_context():
        assert Usuario.query.filter_by(correo='juan@test.com').count() == 1


def test_registro_rechaza_correo_duplicado(client, usuario_empresa):
    respuesta = client.post('/registro', data={
        'nombre_completo': 'Otro Usuario',
        'nombre_usuario': 'otrousuario',
        'correo': usuario_empresa['correo'],  # ya existe
        'password': 'Password123',
        'confirmar_password': 'Password123',
    })

    assert 'ya esta registrado'.encode('utf-8') in respuesta.data


def test_registro_rechaza_passwords_que_no_coinciden(client):
    respuesta = client.post('/registro', data={
        'nombre_completo': 'Juan Perez',
        'nombre_usuario': 'juanperez2',
        'correo': 'juan2@test.com',
        'password': 'Password123',
        'confirmar_password': 'OtraClave456',
    })

    assert 'no coinciden'.encode('utf-8') in respuesta.data


def test_login_exitoso(client, usuario_empresa):
    respuesta = client.post('/login', data={
        'correo': usuario_empresa['correo'],
        'password': usuario_empresa['password'],
    }, follow_redirects=True)

    assert respuesta.status_code == 200


def test_login_rechaza_password_incorrecta(client, usuario_empresa):
    respuesta = client.post('/login', data={
        'correo': usuario_empresa['correo'],
        'password': 'password-incorrecta',
    })

    assert 'incorrectos'.encode('utf-8') in respuesta.data


def test_ruta_privada_redirige_a_login_sin_sesion(client):
    respuesta = client.get('/', follow_redirects=False)

    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers['Location']
