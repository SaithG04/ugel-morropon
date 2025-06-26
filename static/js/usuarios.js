// Espera a que todo el contenido del DOM se haya cargado antes de ejecutar el código
document.addEventListener('DOMContentLoaded', () => {

  // Obtiene referencias a los campos de entrada del formulario
  const nombreInput = document.getElementById('nombre');        // Campo para el nombre
  const institucionInput = document.getElementById('institucion');  // Campo para la institución
  const claveInput = document.getElementById('clave');          // Campo donde se generará la clave

  // Función que genera la clave automáticamente
  function generarClave() {
    // Obtiene los valores ingresados, eliminando espacios y convirtiendo a minúsculas
    const nombre = nombreInput.value.trim().toLowerCase();
    const institucion = institucionInput.value.trim().toLowerCase();

    // Solo genera la clave si ambos campos tienen al menos 3 caracteres
    if (nombre.length >= 3 && institucion.length >= 3) {
      const aleatorio = Math.floor(100 + Math.random() * 900); // Número aleatorio de 3 cifras (entre 100 y 999)

      // Genera la clave: primeras 3 letras del nombre + primeras 3 letras de la institución + número aleatorio
      const clave = nombre.substring(0, 3) + institucion.substring(0, 3) + aleatorio;

      // Asigna la clave generada al campo correspondiente
      claveInput.value = clave;
    } else {
      // Si los campos son muy cortos, deja el campo de clave vacío
      claveInput.value = '';
    }
  }

  // Escucha los cambios en el campo nombre y vuelve a generar la clave
  nombreInput.addEventListener('input', generarClave);

  // Escucha los cambios en el campo institución y vuelve a generar la clave
  institucionInput.addEventListener('input', generarClave);
});
