/*
 * Panel "Actividad reciente" del dashboard.
 * Consulta /dashboard/actividad cada 15 segundos y vuelve a dibujar la lista
 * de ultimas ventas. Las ventas nuevas aparecen resaltadas un momento.
 * Solo consulta mientras la pestana esta visible.
 */
(function () {
    var lista = document.getElementById('actividadLista');
    if (!lista) { return; }

    var URL = lista.getAttribute('data-url');
    var URL_DETALLE = lista.getAttribute('data-detalle-url'); // termina en /0
    var vacio = document.getElementById('actividadVacia');
    var INTERVALO_MS = 15 * 1000;

    function idsActuales() {
        var ids = {};
        lista.querySelectorAll('.actividad-item').forEach(function (li) {
            ids[li.getAttribute('data-id')] = true;
        });
        return ids;
    }

    function crear(etiqueta, clase, texto) {
        var el = document.createElement(etiqueta);
        el.className = clase;
        if (texto !== undefined) { el.textContent = texto; }
        return el;
    }

    function capitalizar(t) {
        return t ? t.charAt(0).toUpperCase() + t.slice(1) : '';
    }

    function crearItem(v, esNueva) {
        var li = crear('li', 'actividad-item' + (esNueva ? ' actividad-nueva' : ''));
        li.setAttribute('data-id', v.id);

        var a = crear('a', 'actividad-link');
        a.href = URL_DETALLE.replace(/0$/, String(v.id));

        var info = crear('div', 'actividad-info');
        info.appendChild(crear('p', 'actividad-titulo', v.titulo));
        info.appendChild(crear('p', 'actividad-meta',
            v.fecha + ' · ' + v.unidades + (v.unidades === 1 ? ' unidad' : ' unidades')));

        var lado = crear('div', 'actividad-lado');
        lado.appendChild(crear('p', 'actividad-total', v.total));
        lado.appendChild(crear('span', 'actividad-estado actividad-estado-' + v.estado, capitalizar(v.estado)));

        a.appendChild(info);
        a.appendChild(lado);
        li.appendChild(a);
        return li;
    }

    function dibujar(ventas) {
        var anteriores = idsActuales();
        var hayAnteriores = Object.keys(anteriores).length > 0;
        var fragmento = document.createDocumentFragment();

        ventas.forEach(function (v) {
            var esNueva = hayAnteriores && !anteriores[String(v.id)];
            fragmento.appendChild(crearItem(v, esNueva));
        });

        lista.innerHTML = '';
        lista.appendChild(fragmento);
        if (vacio) { vacio.classList.toggle('d-none', ventas.length > 0); }
    }

    function consultar() {
        if (document.hidden) { return; }
        fetch(URL, { headers: { 'Accept': 'application/json' }, credentials: 'same-origin' })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (datos) { if (datos && datos.ventas) { dibujar(datos.ventas); } })
            .catch(function () { /* sin conexion: se reintenta en el siguiente ciclo */ });
    }

    setInterval(consultar, INTERVALO_MS);
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) { consultar(); }
    });
})();
