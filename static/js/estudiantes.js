// static/js/estudiantes.js
// Espera que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
  
  // Agrega un listener al input de tipo archivo con ID "importarArchivo"
  document.getElementById('importarArchivo').addEventListener('change', function(e) {
    const file = e.target.files[0]; // Obtiene el primer archivo seleccionado
    if (!file) return; // Si no hay archivo, termina la función

    const reader = new FileReader(); // Crea un lector de archivos

    // Cuando se carga el archivo
    reader.onload = function(e) {
      const data = new Uint8Array(e.target.result); // Convierte los datos del archivo a Uint8Array
      const workbook = XLSX.read(data, { type: 'array' }); // Usa XLSX para leer el archivo Excel

      // Toma la primera hoja del libro
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      
      // Convierte la hoja a un array de arrays (matriz)
      const json = XLSX.utils.sheet_to_json(sheet, { header: 1 });

      const preview = document.getElementById("preview");
      preview.innerHTML = ""; // Limpia la vista previa previa

      // Si la hoja está vacía o no tiene datos
      if (json.length === 0) {
        preview.textContent = "El archivo está vacío o no tiene datos legibles.";
        return;
      }

      // Crea una tabla con clases Bootstrap
      const table = document.createElement("table");
      table.classList.add("table", "table-striped", "table-hover", "table-bordered");

      const thead = document.createElement("thead");
      const tbody = document.createElement("tbody");

      // Recorre cada fila del Excel
      json.forEach((row, rowIndex) => {
        const tr = document.createElement("tr"); // Crea una fila

        row.forEach(cell => {
          // Usa <th> para la primera fila (cabecera), <td> para las demás
          const cellElement = document.createElement(rowIndex === 0 ? "th" : "td");
          cellElement.textContent = cell; // Asigna el valor de la celda
          tr.appendChild(cellElement); // Agrega la celda a la fila
        });

        // Si es la primera fila, va al thead; el resto al tbody
        if (rowIndex === 0) {
          thead.appendChild(tr);
        } else {
          tbody.appendChild(tr);
        }
      });

      // Agrega cabecera y cuerpo a la tabla
      table.appendChild(thead);
      table.appendChild(tbody);

      // Inserta la tabla en el contenedor de vista previa
      preview.appendChild(table);
    };

    // Lee el archivo como ArrayBuffer para procesarlo con XLSX
    reader.readAsArrayBuffer(file);
  });
});
