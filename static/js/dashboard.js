// Espera a que todo el DOM esté cargado antes de ejecutar funciones
document.addEventListener('DOMContentLoaded', () => {

    // Cargar una vista HTML parcial dentro de un contenedor
    function cargarVista(url) {
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error("No se pudo cargar el contenido.");
                }
                return response.text(); // Devuelve el HTML
            })
            .then(data => {
                document.getElementById("main-content").innerHTML = data;
            })
            .catch(error => {
                document.getElementById("main-content").innerHTML = `
                    <div class="alert alert-danger mt-3">
                        <strong>Error:</strong> ${error.message}
                    </div>`;
            });
    }

    // Recarga la página actual (útil para botón "Inicio")
    function mostrarInicio() {
        location.reload();
    }

    // Hace públicas estas funciones para usarlas en HTML
    window.cargarVista = cargarVista;
    window.mostrarInicio = mostrarInicio;

    // Protección contra inspección (bloquea clic derecho y teclas peligrosas)
    const redirectURL = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQIRW5IsZOudQmVobxbJs4CcbYUIfFz-kmFg&s';

    window.addEventListener('contextmenu', e => {
        e.preventDefault();
        window.location.href = redirectURL;
    });

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

    // Inicializa gráfico con Chart.js si existe el canvas
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

        new Chart(ctx, config);
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

// Función para filtrar por estado
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
        "resueltos": "Resuelto"
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
        if (!data || data.length === 0) return;

        const html = data.map(item => {
            const tipo = item.tipo ? item.tipo.toLowerCase() : 'infraestructura'; // ✔️ CORREGIDO
            return `
                <div class="card mb-3 shadow-sm">
                    <div class="card-body position-relative">
                        <div class="position-absolute top-0 end-0 m-2">
<button class="btn btn-sm btn-outline-primary me-1" onclick="verIncidentePorNombre('${item.institucion}', '${tipo}')" title="Ver">
                                <i class="bi bi-eye"></i>
                            </button>
               <button class="btn btn-sm btn-outline-primary me-1" onclick="editarIncidentePorNombre('${tipo}', '${item.institucion}')" title="Editar">
  <i class="bi bi-pencil"></i> Editar
</button>


                        </div>
                        <h6 class="fw-bold mb-1">${item.institucion}</h6>
                        <p class="mb-1"><strong>Registrado por:</strong> ${item.registrado_por}</p>
                        <p class="mb-1"><strong>Correo:</strong> ${item.correo}</p>
                        <p class="mb-1"><strong>Estado:</strong> ${item.estado}</p>
                        <span class="badge bg-primary">${item.tipo}</span>
                    </div>
                </div>
            `;
        }).join("");

        contenedor.innerHTML = html;
    })
    .catch(err => {
        const timestamp = new Date().toLocaleString();
        contenedor.innerHTML = `
            <div class='alert alert-danger'>
                <strong><i class="bi bi-bug"></i> Se produjo un error</strong><br>
                <small><code>${err.message}</code></small><br>
                <span class="text-muted">(${timestamp})</span>
            </div>`;
        console.error("🧯 Error al filtrar por estado:", err);
    });
}

function verIncidentePorNombre(nombre, tipo) {
    if (!nombre || !tipo || tipo === "undefined" || tipo === "null") {
        const detalle = `⚠️ Parámetros inválidos recibidos:\n• nombre: ${nombre} (${typeof nombre})\n• tipo: ${tipo} (${typeof tipo})`;
        alert("Información del incidente inválida. No se puede visualizar.\n\n" + detalle);
        console.warn("🛑 verIncidentePorNombre fue llamado con parámetros inválidos:", { nombre, tipo });
        return;
    }

    console.log("📡 Consultando incidente:", `/api/incidente_por_nombre/${tipo}/${encodeURIComponent(nombre)}`);

    fetch(`/api/incidente_por_nombre/${tipo}/${encodeURIComponent(nombre)}`)
        .then(res => {
            if (!res.ok) throw new Error(`No se pudo cargar el incidente. Código HTTP: ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (!data || typeof data !== "object") throw new Error("Respuesta del servidor inválida");

            document.getElementById("verInstitucion").textContent = data.institucion || 'No disponible';
            document.getElementById("verRegistradoPor").textContent = data.registrado_por || 'No disponible';
            document.getElementById("verCorreo").textContent = data.correo || 'No disponible';
            document.getElementById("verTelefono").textContent = data.telefono || 'No disponible';
            document.getElementById("verEstado").textContent = data.estado || 'No disponible';
            document.getElementById("verTipo").textContent = data.tipo || 'No disponible';
            document.getElementById("verDescripcion").textContent = data.descripcion || 'Sin descripción';

            const modalEl = document.getElementById("modalVerIncidente");
            if (!modalEl) {
                console.error("🛑 No se encontró el modal");
                alert("No se puede mostrar el modal.");
                return;
            }

            new bootstrap.Modal(modalEl).show();
        })
        .catch(err => {
            console.error("🚨 Error al obtener el incidente:", err);
            alert(`No se pudo cargar la información del incidente:\n${err.message}`);
        });
}
const tipoNormalizado = tipo.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
verIncidente(id, tipoNormalizado); // evita pasar "académico"

document.getElementById("formEditarIncidente").addEventListener("submit", e => {
    e.preventDefault();

    const id = document.getElementById("editarId").value;
    const datos = {
        institucion: document.getElementById("editarInstitucion").value,
        correo: document.getElementById("editarCorreo").value,
        telefono: document.getElementById("editarTelefono").value,
        estado: document.getElementById("editarEstado").value,
        descripcion: document.getElementById("editarDescripcion").value
    };

    fetch(`/api/actualizar_incidente/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos)
    })
    .then(res => {
        if (!res.ok) throw new Error("No se pudo guardar los cambios");
        return res.json();
    })
    .then(resp => {
        const modal = bootstrap.Modal.getInstance(document.getElementById("modalEditarIncidente"));
        modal.hide();
        alert("✅ Incidente actualizado con éxito");

        if (typeof filtrarPorEstado === "function") filtrarPorEstado();
    })
    .catch(err => {
        console.error("🛑 Error al guardar:", err);
        alert("❌ Error al actualizar el incidente.");
    });
});
function editarIncidentePorNombre(tipo, nombre) {
    if (!nombre || !tipo || tipo === "undefined" || tipo === "null") {
        const detalle = `⚠️ Parámetros inválidos recibidos:\n• nombre: ${nombre} (${typeof nombre})\n• tipo: ${tipo} (${typeof tipo})`;
        alert("Información inválida para editar el incidente.\n\n" + detalle);
        console.warn("🛑 editarIncidentePorNombre fue llamado con parámetros inválidos:", { nombre, tipo });
        return;
    }

    const url = `/api/incidente_por_nombre/${tipo}/${encodeURIComponent(nombre)}`;
    console.log("✏️ Consultando incidente para editar:", url);

    fetch(url)
        .then(res => {
            if (!res.ok) throw new Error(`No se pudo cargar el incidente. Código HTTP: ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (!data || typeof data !== "object") throw new Error("Respuesta inválida del servidor");

            document.getElementById("editarId").value = data.id || '';
            document.getElementById("editarInstitucion").value = data.institucion || '';
            document.getElementById("editarCorreo").value = data.correo || '';
            document.getElementById("editarTelefono").value = data.telefono || '';
            document.getElementById("editarEstado").value = data.estado || 'Pendiente';
            document.getElementById("editarDescripcion").value = data.descripcion || '';

            const modalEditar = new bootstrap.Modal(document.getElementById("modalEditarIncidente"));
            modalEditar.show();
        })
        .catch(err => {
            const timestamp = new Date().toLocaleString();
            const mensaje = `
❌ Error al intentar cargar el incidente para editar.

🕒 Fecha/Hora: ${timestamp}
📍 Endpoint: ${url}

💥 Error: ${err.message}
🧠 Stack trace:
${err.stack || 'No disponible'}

Verifica si el backend está respondiendo correctamente o si los datos están mal formados.
            `;
            console.error("🚨 Detalle completo del error:", err);
            alert(mensaje);
        });
}
