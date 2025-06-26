// Espera a que todo el DOM esté cargado antes de ejecutar funciones
document.addEventListener('DOMContentLoaded', () => {

    // ----------------------------------------
    // Cargar una vista HTML parcial dentro de un contenedor
    // ----------------------------------------
    function cargarVista(url) {
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error("No se pudo cargar el contenido.");
                }
                return response.text(); // Devuelve el HTML
            })
            .then(data => {
                // Inserta el contenido HTML recibido en el contenedor principal
                document.getElementById("main-content").innerHTML = data;
            })
            .catch(error => {
                // Muestra un mensaje de error dentro del contenedor
                document.getElementById("main-content").innerHTML = `
                    <div class="alert alert-danger mt-3">
                        <strong>Error:</strong> ${error.message}
                    </div>`;
            });
    }

    // ----------------------------------------
    // Recarga la página actual (útil para botón "Inicio")
    // ----------------------------------------
    function mostrarInicio() {
        location.reload();
    }

    // ----------------------------------------
    // Hace públicas estas funciones para usarlas en HTML
    // ----------------------------------------
    window.cargarVista = cargarVista;
    window.mostrarInicio = mostrarInicio;

    // ----------------------------------------
    // Protección contra inspección (bloquea clic derecho y teclas peligrosas)
    // ----------------------------------------
    const redirectURL = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQIRW5IsZOudQmVobxbJs4CcbYUIfFz-kmFg&s';

    // Bloquea clic derecho
    window.addEventListener('contextmenu', e => {
        e.preventDefault();
        window.location.href = redirectURL;
    });

    // Bloquea atajos como F12, Ctrl+Shift+I, Ctrl+U, etc.
    window.addEventListener('keydown', e => {
        if (
            e.key === 'F12' ||
            (e.ctrlKey && e.shiftKey && ['I', 'J', 'C'].includes(e.key.toUpperCase())) ||
            (e.ctrlKey && ['U', 'S', 'H', 'A', 'F'].includes(e.key.toUpperCase()))
        ) {
            e.preventDefault();
            window.location.href = redirectURL;
        }
    });

    // ----------------------------------------
    // Inicializa gráfico con Chart.js si existe el canvas
    // ----------------------------------------
    const ctx = document.getElementById('graficoIncidentes');
    if (ctx) {
        const data = {
            labels: ['Resueltos', 'En Proceso', 'Sin Resolver'],
            datasets: [{
                label: 'Incidentes por Estado',
                data: [
                    parseInt(ctx.dataset.resueltos),
                    parseInt(ctx.dataset.enProceso),
                    parseInt(ctx.dataset.total) - (
                        parseInt(ctx.dataset.resueltos) + parseInt(ctx.dataset.enProceso)
                    )
                ],
                backgroundColor: ['#198754', '#ffc107', '#dc3545'],
                borderWidth: 1
            }]
        };

        const config = {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true },
                    title: {
                        display: true,
                        text: 'Distribución de Incidentes'
                    }
                }
            }
        };

        new Chart(ctx, config); // Renderiza el gráfico
    }

}); // Fin del DOMContentLoaded
// Gráfico de barras (absoluto)
const barra = document.getElementById('graficoIncidentes');
if (barra) {
    const total = parseInt(barra.dataset.total);
    const resueltos = parseInt(barra.dataset.resueltos);
    const enProceso = parseInt(barra.dataset.enProceso);
    const pendientes = total - resueltos - enProceso;

    new Chart(barra, {
        type: 'bar',
        data: {
            labels: ['Resueltos', 'En Proceso', 'Pendientes'],
            datasets: [{
                label: 'Cantidad',
                data: [resueltos, enProceso, pendientes],
                backgroundColor: ['#198754', '#ffc107', '#dc3545'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Incidentes por Estado' }
            }
        }
    });
}

// Gráfico de dona (porcentual)
const donut = document.getElementById('graficoPorcentaje');
if (donut) {
    const total = parseInt(donut.dataset.total);
    const resueltos = parseInt(donut.dataset.resueltos);
    const enProceso = parseInt(donut.dataset.enProceso);
    const pendientes = total - resueltos - enProceso;

    const porcentajes = [resueltos, enProceso, pendientes].map(x => Math.round((x / total) * 100));

    new Chart(donut, {
        type: 'doughnut',
        data: {
            labels: [
                `Resueltos (${porcentajes[0]}%)`,
                `En Proceso (${porcentajes[1]}%)`,
                `Pendientes (${porcentajes[2]}%)`
            ],
            datasets: [{
                data: porcentajes,
                backgroundColor: ['#198754', '#ffc107', '#dc3545']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                title: { display: true, text: 'Porcentaje por Estado' }
            }
        }
    });
}
function filtrarPorEstado() {
    const estadoSeleccionado = document.getElementById("selectorEstado").value;
    const contenedor = document.getElementById("resultadosEstado");

    if (!estadoSeleccionado || estadoSeleccionado === "todos") {
        contenedor.innerHTML = `
            <p class="text-muted">
                Seleccione un estado para ver detalles de las instituciones.
            </p>`;
        return;
    }

   const mapaEstados = {
    "pendientes": "Pendiente",
    "en_proceso": "En proceso",
    "resueltos": "Resuelto" // ← Debe ser "Resueltos" (con S)
};

    const estado = mapaEstados[estadoSeleccionado] || "";

    fetch("/filtrar_estado", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado })
    })
  .then(async res => {
    if (res.status === 404) {
        contenedor.innerHTML = `
            <div class='alert alert-warning'>
                <i class="bi bi-exclamation-circle"></i> No se encontraron registros en este estado.
            </div>`;
        return [];
    }

    if (!res.ok) {
        let errorMsg = `Error ${res.status}`;
        try {
            const errorData = await res.json();
            errorMsg += ` - ${errorData.error || "Mensaje no disponible"}`;
        } catch {
            errorMsg += " - No se pudo interpretar el mensaje de error";
        }
        throw new Error(errorMsg);
    }

    return res.json();
})
.then(data => {
    if (!data || data.length === 0) return; // Ya se mostró mensaje de no encontrados si era 404

    const html = data.map(item => `
        <li class="list-group-item d-flex justify-content-between align-items-start flex-column">
            <div><strong>Institución:</strong> ${item.institucion}</div>
            <div><strong>Registrado por:</strong> ${item.registrado_por}</div>
            <div><strong>Correo:</strong> ${item.correo}</div>
            <div><strong>Estado:</strong> ${item.estado}</div>
            <span class="badge bg-primary align-self-end">${item.tipo}</span>
        </li>
    `).join("");

    contenedor.innerHTML = `<ul class='list-group'>${html}</ul>`;
})
    .catch(err => {
        const timestamp = new Date().toLocaleString();
        contenedor.innerHTML = `
            <div class='alert alert-danger'>
                <strong><i class="bi bi-bug"></i> Se produjo un error</strong><br>
                <small><code>${err.message}</code></small><br>
                <span class="text-muted">(${timestamp})</span>
            </div>`;
        console.error("🧯 Detalle del error al filtrar por estado:", err);
    });
}
