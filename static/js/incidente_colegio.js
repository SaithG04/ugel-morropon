console.log('Script incidente_colegios.js cargado');
document.addEventListener('DOMContentLoaded', function () {
  const tipo = document.getElementById('tipo');
  const formIncidencia = document.getElementById('form-incidencia');
  const formInfraestructura = document.getElementById('form-infraestructura');

  if (tipo && formIncidencia && formInfraestructura) {
    tipo.addEventListener('change', function () {
      const valor = tipo.value;

      if (valor === 'incidencia') {
        formIncidencia.classList.remove('d-none');
        formInfraestructura.classList.add('d-none');  
      } else if (valor === 'infraestructura') {
        formInfraestructura.classList.remove('d-none');
        formIncidencia.classList.add('d-none');
      }
    });
  }
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
});
