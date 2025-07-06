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
      // Muestra un mensaje de error en el contenedor si falla la carga
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
 * Filtra las filas de la tabla de incidentes según el tipo seleccionado en el filtro.
 */
function filtrarIncidentes() {
  const filtro = document.getElementById('filtroTipo').value;
  const table = document.getElementById('tablaIncidentes');
  const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
  const thead = document.getElementById('tablaIncidentesHead');
  const tablaContainer = document.getElementById('tablaContainer');
  const noResultadosInicial = document.getElementById('noResultadosInicial');
  const noResultadosFiltro = document.getElementById('noResultadosFiltro');
  const incidentesContainer = document.getElementById('incidentesContainer');
  const thDescripcion = document.getElementById('thDescripcion');
  const thEstudiante = document.getElementById('thEstudiante');
  const thTipoProblema = document.getElementById('thTipoProblema');

  let hasVisibleRows = false;
  let hasAcademico = false;
  let hasInfraestructura = false;

  // Itera sobre las filas para mostrar u ocultar según el filtro
  for (let row of rows) {
    const tipo = row.getAttribute('data-tipo');
    if (filtro === tipo) {
      row.style.display = '';
      hasVisibleRows = true;
      if (tipo === 'academico') hasAcademico = true;
      if (tipo === 'infraestructura') hasInfraestructura = true;
    } else {
      row.style.display = 'none';
    }
  }

  // Si no hay filtro seleccionado, oculta todas las filas
  if (filtro === '') {
    for (let row of rows) {
      row.style.display = 'none';
    }
    hasVisibleRows = false;
  }

  // Ajusta la visibilidad de las columnas del encabezado según el tipo
  thEstudiante.style.display = hasAcademico ? '' : 'none';
  thTipoProblema.style.display = hasInfraestructura ? '' : 'none';

  // Ajusta las celdas visibles en el cuerpo de la tabla
  for (let row of rows) {
    if (row.style.display === 'none') continue;
    const tipo = row.getAttribute('data-tipo');
    const cells = row.getElementsByTagName('td');
    cells[2].style.display = (tipo === 'academico') ? '' : 'none'; // Estudiante
    cells[3].style.display = (tipo === 'infraestructura') ? '' : 'none'; // Tipo de problema
  }

  // Cambia el texto del encabezado "Descripción" a "Motivo" si el filtro es académico
  if (filtro === 'academico') {
    thDescripcion.textContent = 'Motivo';
  } else {
    thDescripcion.textContent = 'Descripción';
  }

  // Controla la visibilidad de la tabla y los mensajes según los resultados
  if (filtro === '' && incidentesContainer) {
    tablaContainer.style.display = 'none';
    noResultadosInicial.style.display = '';
    noResultadosFiltro.style.display = 'none';
  } else if (hasVisibleRows) {
    tablaContainer.style.display = '';
    noResultadosInicial.style.display = 'none';
    noResultadosFiltro.style.display = 'none';
  } else {
    tablaContainer.style.display = 'none';
    noResultadosInicial.style.display = 'none';
    noResultadosFiltro.style.display = '';
  }
}

/**
 * Abre el modal de edición y carga los datos del incidente seleccionado.
 * @param {string} id - ID del incidente.
 * @param {string} tipo - Tipo de incidente (academico o infraestructura).
 */
function abrirModalEditar(id, tipo) {
  // Valida los parámetros recibidos
  if (!id || !tipo || tipo === "undefined" || tipo === "null") {
    const detalle = `Parámetros inválidos recibidos:\n• id: ${id} (${typeof id})\n• tipo: ${tipo} (${typeof tipo})`;
    alert("Información inválida para editar el incidente.\n\n" + detalle);
    console.warn("abrirModalEditar fue llamado con parámetros inválidos:", { id, tipo });
    return;
  }

  const labelDescripcion = document.getElementById("labelEditarDescripcion");
  const tipoNormalizado = tipo.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const url = `/api/incidente_por_id/${id}/${tipoNormalizado}`;

  // Realiza la solicitud al servidor para obtener los datos del incidente
  fetch(url)
    .then(res => {
      if (!res.ok) throw new Error(`No se pudo cargar el incidente. Código HTTP: ${res.status}`);
      return res.json();
    })
    .then(data => {
      if (!data || typeof data !== "object" || !data.id) {
        throw new Error("Respuesta inválida del servidor: datos incompletos o sin ID");
      }

      // Rellena los campos comunes del formulario
      document.getElementById("editarId").value = data.id || '';
      document.getElementById("editarTipo").value = data.tipo || tipoNormalizado;
      document.getElementById("editarInstitucion").value = data.institucion || '';
      document.getElementById("editarCorreo").value = data.correo || '';
      document.getElementById("editarTelefono").value = data.telefono || '';
      document.getElementById("editarEstado").value = data.estado || 'Pendiente';
      document.getElementById("editarComentarios").value = data.comentarios || '';

      // Ajusta los campos condicionales según el tipo de incidente
      const divEstudiante = document.getElementById("divEstudiante");
      const divTipoProblema = document.getElementById("divTipoProblema");
      const editarEstudiante = document.getElementById("editarEstudiante");
      const editarTipoProblema = document.getElementById("editarTipoProblema");
      const inputDescripcion = document.getElementById("editarDescripcion");

      if (tipoNormalizado === "academico") {
        divEstudiante.style.display = '';
        divTipoProblema.style.display = 'none';
        editarEstudiante.value = data.nombre_estudiante || 'Sin estudiante';
        editarTipoProblema.value = '';
        labelDescripcion.textContent = 'Motivo';
        inputDescripcion.value = data.motivo || '';
      } else if (tipoNormalizado === "infraestructura") {
        divEstudiante.style.display = 'none';
        divTipoProblema.style.display = '';
        editarEstudiante.value = '';
        editarTipoProblema.value = data.problema || 'Sin tipo';
        labelDescripcion.textContent = 'Descripción';
        inputDescripcion.value = data.descripcion || '';
      } else {
        labelDescripcion.textContent = 'Descripción';
        inputDescripcion.value = '';
      }

      // Muestra el modal de edición
      const modalEditar = new bootstrap.Modal(document.getElementById("modalEditarIncidente"));
      modalEditar.show();
    })
    .catch(err => {
      // Muestra un mensaje detallado en caso de error
      const timestamp = new Date().toLocaleString();
      const mensaje = `
Error al intentar cargar el incidente para editar.

Fecha/Hora: ${timestamp}
Endpoint: ${url}

Error: ${err.message}
Stack trace: ${err.stack || 'No disponible'}

Verifica si el backend está respondiendo correctamente o si los datos están mal formados.
      `;
      console.error("Detalle completo del error:", err);
      alert(mensaje);
    });
}

// Asocia funciones al objeto window para que sean accesibles desde HTML
window.cargarVista = cargarVista;
window.mostrarInicio = mostrarInicio;
window.filtrarIncidentes = filtrarIncidentes;
window.abrirModalEditar = abrirModalEditar;

// Inicializa el filtrado de incidentes al cargar la página
document.addEventListener('DOMContentLoaded', filtrarIncidentes);

/**
 * Configura el evento de envío del formulario de edición al cargar la página.
 */
document.addEventListener('DOMContentLoaded', () => {
  const formEditarIncidente = document.getElementById("formEditarIncidente");
  if (formEditarIncidente) {
    formEditarIncidente.addEventListener("submit", e => {
      e.preventDefault();

      const id = document.getElementById("editarId").value;
      if (!id) {
        console.error("No se proporcionó un ID de incidente");
        alert("No se proporcionó un ID de incidente");
        return;
      }

      // Normaliza el tipo de incidente
      const tipo = document.getElementById("editarTipo").value?.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

      // Construye el objeto de datos a enviar
      const datos = {
        tipo_incidente: tipo,
        institucion: document.getElementById("editarInstitucion").value,
        correo: document.getElementById("editarCorreo").value,
        telefono: document.getElementById("editarTelefono").value,
        estado: document.getElementById("editarEstado").value,
        comentarios: document.getElementById("editarComentarios").value,
        nombre_estudiante: document.getElementById("editarEstudiante").value || null,
        tipo_problema: document.getElementById("editarTipoProblema").value || null
      };

      const descripcionOequivalente = document.getElementById("editarDescripcion").value || '';
      if (tipo === "academico") {
        datos.motivo = descripcionOequivalente;
      } else if (tipo === "infraestructura") {
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
          console.error("Error al guardar:", err);
          alert(`Error al actualizar el incidente: ${err.message}`);
        });
    });
  }

  // Protección contra clic derecho
  const redirectURL = 'https://encrypted-tbn0.gstatic.com/images?q=tbn9GcRQIRW5IsZOudQmVobxbJs4CcbYUIfFz-kmFg&s';
  window.addEventListener('contextmenu', e => {
    e.preventDefault();
    window.location.href = redirectURL;
  });
});