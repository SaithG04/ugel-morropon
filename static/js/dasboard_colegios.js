
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

// Función para refrescar la página al dar clic en "Inicio"
function mostrarInicio() {
  location.reload();
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
