document.addEventListener("DOMContentLoaded", function () {
  const selectInstitucion = document.getElementById("selectInstitucion");
  const preview = document.getElementById("preview");

  selectInstitucion.addEventListener("change", () => {
    const institucion = selectInstitucion.value;

    preview.innerHTML = `<div class="text-center my-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div></div>`;

    fetch("/api/evidencias", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ institucion }),
    })
      .then(response => response.json())
      .then(data => {
        if (data.length === 0) {
          preview.innerHTML = `<div class="alert alert-warning">No hay evidencias registradas para esta institución.</div>`;
        } else {
          let html = `
            <table class="table table-bordered table-hover">
              <thead class="table-dark">
                <tr>
                  <th>Tipo</th>
                  <th>Estudiante</th>
                  <th>Motivo</th>
                  <th>Fecha</th>
                  <th>Hora</th>
                  <th>Estado</th>
                  <th>Institución</th>
                  <th>Evidencia</th>
                </tr>
              </thead>
              <tbody>
          `;
          data.forEach(row => {
            html += `
              <tr>
                <td>${row.tipo}</td>
                <td>${row.nombre_estudiante || '-'}</td>
                <td>${row.motivo}</td>
                <td>${row.fecha}</td>
                <td>${row.hora}</td>
                <td>${row.estado}</td>
                <td>${row.institucion}</td>
                <td>
                  ${row.evidencia ? `<a href="${row.evidencia}" target="_blank">Ver imagen</a>` : "No hay"}
                </td>
              </tr>
            `;
          });
          html += "</tbody></table>";
          preview.innerHTML = html;
        }
      })
      .catch(error => {
        preview.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
      });
  });
});
