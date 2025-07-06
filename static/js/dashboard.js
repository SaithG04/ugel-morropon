// Espera a que el DOM esté completamente cargado antes de ejecutar el código
document.addEventListener('DOMContentLoaded', () => {
    /**
     * Carga una vista dinámica en el contenedor principal mediante fetch.
     * @param {string} url - URL del contenido a cargar.
     */
    function cargarVista(url) {
        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error("No se pudo cargar el contenido.");
                return response.text();
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

    /**
     * Recarga la página para volver a la vista inicial.
     */
    function mostrarInicio() {
        location.reload();
    }

    /**
     * Filtra incidentes por estado y muestra los resultados en el contenedor.
     */
    function filtrarPorEstado() {
        const estadoSeleccionado = document.getElementById("selectorEstado").value;
        const contenedor = document.getElementById("resultadosEstado");

        if (!estadoSeleccionado || estadoSeleccionado === "todos") {
            contenedor.innerHTML = `
        <p class="text-muted">Seleccione un estado para ver detalles de las instituciones.</p>`;
            return;
        }

        const mapaEstados = {
            "pendientes": "Pendiente",
            "en_proceso": "En proceso",
            "resueltos": "Resuelto"
        };

        const estado = mapaEstados[estadoSeleccionado] || "";

        // Realiza la solicitud al servidor para filtrar por estado
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

                // Genera el HTML para mostrar los resultados
                const html = data.map(item => {
                    const tipo = item.tipo ? item.tipo.toLowerCase() : 'infraestructura';
                    const tipoNormalizado = tipo.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                    return `
            <div class="card mb-3 shadow-sm">
              <div class="card-body position-relative">
                <div class="position-absolute top-0 end-0 m-2">
                  <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModalVer('${item.id}', '${tipoNormalizado}')" title="Ver">
                    <i class="bi bi-eye"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModalEditar('${item.id}', '${tipoNormalizado}')" title="Editar">
                    <i class="bi bi-pencil"></i> Editar
                  </button>
                </div>
                <h6 class="fw-bold mb-1">ID: ${item.id}</h6>
                <p class="mb-1"><strong>Institución:</strong> ${item.institucion}</p>
                <p class="mb-1"><strong>Fecha:</strong> ${item.fecha}</p>
                <p class="mb-1"><strong>Registrado por:</strong> ${item.registrado_por}</p>
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
                console.error("Error al filtrar por estado:", err);
            });
    }

    /**
     * Abre el modal para ver los detalles de un incidente por ID.
     * @param {string} id - ID del incidente.
     * @param {string} tipo - Tipo de incidente.
     */
    function abrirModalVer(id, tipo) {
        fetch(`/api/incidente_por_id/${id}/${tipo}`)
            .then(res => res.json())
            .then(data => {
                // Rellena los campos del modal de visualización
                document.getElementById("verInstitucion").textContent = data.institucion || 'No disponible';
                document.getElementById("verRegistradoPor").textContent = data.registrado_por || 'No disponible';
                document.getElementById("verCorreo").textContent = data.correo || 'No disponible';
                document.getElementById("verTelefono").textContent = data.telefono || 'No disponible';
                document.getElementById("verEstado").textContent = data.estado || 'No disponible';
                const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);
                document.getElementById("verTipo").textContent = capitalize(data.tipo) || 'No disponible';
                //document.getElementById("verDescripcion").textContent = data.descripcion || 'Sin descripción';
                document.getElementById("verComentarios").textContent = data.comentarios || 'Sin comentarios';

                // Ajusta la visibilidad de campos condicionales
                document.getElementById("verEstudianteContainer").style.display = tipo === "academico" ? '' : 'none';
                document.getElementById("verTipoProblemaContainer").style.display = tipo === "infraestructura" ? '' : 'none';
                document.getElementById("verDescripcionLabel").textContent = tipo === "infraestructura" ? 'Descripción:' : 'Motivo:';
                document.getElementById("verDescripcion").textContent = tipo === "infraestructura" ? data.descripcion || 'Sin descripción' : data.motivo || 'Sin motivo';
                document.getElementById("verEstudiante").textContent = data.nombre_estudiante || 'Sin estudiante';
                document.getElementById("verTipoProblema").textContent = data.problema || 'Sin tipo';

                // Muestra el modal
                new bootstrap.Modal(document.getElementById("modalVerIncidente")).show();
            })
            .catch(err => console.error("Error al cargar incidente:", err));
    }

    /**
     * Abre el modal para editar un incidente por ID (con permisos de admin).
     * @param {string} id - ID del incidente.
     * @param {string} tipo - Tipo de incidente.
     */
    function abrirModalEditar(id, tipo) {
        fetch(`/api/incidente_por_id/${id}/${tipo}`)
            .then(res => res.json())
            .then(data => {
                // Rellena los campos del formulario de edición
                document.getElementById("editarId").value = data.id || '';
                document.getElementById("editarTipo").value = tipo;
                document.getElementById("editarInstitucion").value = data.institucion || '';
                document.getElementById("editarCorreo").value = data.correo || '';
                document.getElementById("editarEstado").value = data.estado || 'Pendiente';
                //document.getElementById("editarDescripcion").value = data.descripcion || data.motivo || '';
                document.getElementById("editarComentarios").value = data.comentarios || '';

                // Ajusta la visibilidad y valores de campos condicionales
                document.getElementById("editarEstudianteContainer").style.display = tipo === "academico" ? '' : 'none';
                document.getElementById("editarTipoProblemaContainer").style.display = tipo === "infraestructura" ? '' : 'none';
                document.getElementById("labelEditarDescripcion").textContent = tipo === "infraestructura" ? 'Descripción' : 'Motivo';
                document.getElementById("editarDescripcion").value = tipo === "infraestructura" ? data.descripcion || '' : data.motivo || '';
                document.getElementById("editarEstudiante").value = data.nombre_estudiante || '';
                document.getElementById("editarTipoProblema").value = data.problema || '';

                // Muestra el modal
                new bootstrap.Modal(document.getElementById("modalEditarIncidente")).show();
            })
            .catch(err => console.error("Error al cargar incidente:", err));
    }

    // Configura el evento de envío del formulario de edición
    const formEditarIncidente = document.getElementById("formEditarIncidente");
    if (formEditarIncidente) {
        formEditarIncidente.addEventListener("submit", e => {
            e.preventDefault();

            const id = document.getElementById("editarId").value;
            const tipo = document.getElementById("editarTipo").value.toLowerCase();
            const tipoNormalizado = tipo.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

            // Construye el objeto de datos a enviar
            const datos = {
                tipo_incidente: tipoNormalizado,
                institucion: document.getElementById("editarInstitucion").value,
                correo: document.getElementById("editarCorreo").value,
                estado: document.getElementById("editarEstado").value,
                comentarios: document.getElementById("editarComentarios").value,
                nombre_estudiante: tipoNormalizado === "academico" ? document.getElementById("editarEstudiante").value : null,
                tipo_problema: tipoNormalizado === "infraestructura" ? document.getElementById("editarTipoProblema").value : null
            };

            const descripcionOequivalente = document.getElementById("editarDescripcion").value || '';
            if (tipoNormalizado === "academico") {
                datos.motivo = descripcionOequivalente;
            } else if (tipoNormalizado === "infraestructura") {
                datos.descripcion = descripcionOequivalente;
            }

            // Envía los datos actualizados al servidor
            fetch(`/api/actualizar_incidente/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(datos)
            })
                .then(async res => {
                    if (!res.ok) {
                        let errorMsg = `Error ${res.status}`;
                        try {
                            const errorData = await res.json();
                            errorMsg = errorData.error || "No se pudo guardar los cambios";
                        } catch {
                            errorMsg = "No se pudo interpretar el mensaje de error";
                        }
                        throw new Error(errorMsg);
                    }
                    return res.json();
                })
                .then(resp => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById("modalEditarIncidente"));
                    modal.hide();
                    alert(resp.message || "Incidente actualizado con éxito");
                    location.reload();
                })
                .catch(err => {
                    console.error("Error al actualizar:", err);
                    alert(`Error al actualizar el incidente: ${err.message}`);
                });
        });
    }

    // Inicializa los gráficos de barras y dona
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
                labels: [`Resueltos (${porcentajes[0]}%)`, `En Proceso (${porcentajes[1]}%)`, `Pendientes (${porcentajes[2]}%)`],
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

    // Asocia funciones al objeto window para acceso global
    window.cargarVista = cargarVista;
    window.mostrarInicio = mostrarInicio;
    window.filtrarPorEstado = filtrarPorEstado;
    window.abrirModalVer = abrirModalVer;
    window.abrirModalEditar = abrirModalEditar;

    // Protección contra clic derecho
    const redirectURL = 'https://encrypted-tbn0.gstatic.com/images?q=tbn9GcRQIRW5IsZOudQmVobxbJs4CcbYUIfFz-kmFg&s';
    window.addEventListener('contextmenu', e => {
        e.preventDefault();
        window.location.href = redirectURL;
    });
});