/*
 * Aviso de "Stock bajo" (abajo a la derecha).
 * Consulta /inventario/alertas/estado cada 5 minutos; si hay productos bajo el
 * minimo, muestra un mensaje con titulo "Stock bajo" y "Revisa el stock".
 * El servidor, al recibir la consulta, tambien se encarga de enviar el correo
 * (maximo 1 por hora por empresa).
 */
(function () {
    var raiz = document.getElementById('stock-alert-root');
    if (!raiz) { return; }

    var URL_ESTADO = raiz.getAttribute('data-url');
    var INTERVALO_MS = 5 * 60 * 1000;   // cada 5 minutos
    var REVISION_MS = 30 * 1000;        // cada cuanto se revisa si ya toca consultar
    var DURACION_AVISO_MS = 15 * 1000;  // cuanto tiempo queda visible el aviso
    var CLAVE = 'stockflow_ultima_consulta_stock';
    var temporizadorCierre = null;

    function leerUltimaConsulta() {
        try { return parseInt(window.sessionStorage.getItem(CLAVE) || '0', 10); }
        catch (e) { return 0; }
    }

    function guardarUltimaConsulta() {
        try { window.sessionStorage.setItem(CLAVE, String(Date.now())); }
        catch (e) { /* sin sessionStorage: se consulta igual en cada carga */ }
    }

    function cerrarAviso() {
        var existente = document.getElementById('stock-toast');
        if (existente) { existente.parentNode.removeChild(existente); }
        if (temporizadorCierre) { clearTimeout(temporizadorCierre); temporizadorCierre = null; }
    }

    function mostrarAviso(datos) {
        cerrarAviso();

        var nombres = datos.productos.map(function (p) { return p.nombre; });
        var resto = datos.count - nombres.length;
        var detalle = nombres.join(', ') + (resto > 0 ? ' y ' + resto + ' mas' : '');

        var aviso = document.createElement('div');
        aviso.id = 'stock-toast';
        aviso.className = 'stock-toast';
        aviso.setAttribute('role', 'alert');
        aviso.setAttribute('aria-live', 'assertive');

        var cabecera = document.createElement('div');
        cabecera.className = 'stock-toast-header';

        var titulo = document.createElement('strong');
        titulo.textContent = '⚠ Stock bajo';

        var cerrar = document.createElement('button');
        cerrar.type = 'button';
        cerrar.className = 'stock-toast-close';
        cerrar.setAttribute('aria-label', 'Cerrar');
        cerrar.textContent = '×';
        cerrar.addEventListener('click', cerrarAviso);

        cabecera.appendChild(titulo);
        cabecera.appendChild(cerrar);

        var cuerpo = document.createElement('div');
        cuerpo.className = 'stock-toast-body';

        var mensaje = document.createElement('p');
        mensaje.className = 'mb-1';
        mensaje.textContent = 'Revisa el stock. ' + datos.count +
            (datos.count === 1 ? ' producto esta' : ' productos estan') + ' bajo el minimo: ' + detalle + '.';

        var enlace = document.createElement('a');
        enlace.href = datos.url_alertas;
        enlace.textContent = 'Ver alertas de stock';

        cuerpo.appendChild(mensaje);
        cuerpo.appendChild(enlace);

        aviso.appendChild(cabecera);
        aviso.appendChild(cuerpo);
        document.body.appendChild(aviso);

        temporizadorCierre = setTimeout(cerrarAviso, DURACION_AVISO_MS);
    }

    function consultar() {
        guardarUltimaConsulta();
        fetch(URL_ESTADO, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
            .then(function (respuesta) { return respuesta.ok ? respuesta.json() : null; })
            .then(function (datos) {
                if (datos && datos.count > 0) { mostrarAviso(datos); }
            })
            .catch(function () { /* sin conexion: se reintenta en la proxima revision */ });
    }

    function revisarSiToca() {
        if (Date.now() - leerUltimaConsulta() >= INTERVALO_MS) { consultar(); }
    }

    revisarSiToca();
    setInterval(revisarSiToca, REVISION_MS);
})();
