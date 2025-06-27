// static/js/incidente.js
// Espera a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
  // Referencias a los elementos HTML
  const tipoSelect = document.getElementById('tipo'); // Selector de tipo de incidente
  const formIncidencia = document.getElementById('form-incidencia'); // Formulario de incidencia académica
  const formInfraestructura = document.getElementById('form-infraestructura'); // Formulario de infraestructura

  // Evento cuando el usuario cambia el tipo de incidente
  tipoSelect.addEventListener('change', () => {
    // Oculta ambos formularios al principio
    formIncidencia.classList.add('d-none');
    formInfraestructura.classList.add('d-none');

    // Muestra el formulario correspondiente según la opción seleccionada
    if (tipoSelect.value === 'incidencia') {
      formIncidencia.classList.remove('d-none'); // Muestra formulario académico
    } else if (tipoSelect.value === 'infraestructura') {
      formInfraestructura.classList.remove('d-none'); // Muestra formulario infraestructura
    }
  });
});
