// static/js/login.js
// Función para mostrar u ocultar la contraseña
function togglePassword() {
    const passwordInput = document.getElementById("clave");     // Input de contraseña
    const toggleIcon = document.getElementById("toggleIcon");   // Ícono de ojo (para cambiar entre mostrar y ocultar)

    if (passwordInput.type === "password") {
        // Mostrar la contraseña
        passwordInput.type = "text";
        toggleIcon.classList.remove("fa-eye");
        toggleIcon.classList.add("fa-eye-slash");
    } else {
        // Ocultar la contraseña
        passwordInput.type = "password";
        toggleIcon.classList.remove("fa-eye-slash");
        toggleIcon.classList.add("fa-eye");
    }
}

// Función para prevenir scraping, copia e inspección del código
function prevenirScraping() {
    const redirectUrl = "https://www.shutterstock.com/image-vector/access-denied-prohibition-sign-used-260nw-2097202471.jpg";
    // Imagen o página a la que se redirige si se detecta intento de inspección

    // Desactiva el clic derecho
    document.addEventListener("contextmenu", e => e.preventDefault());

    // Desactiva la selección de texto
    document.addEventListener("selectstart", e => e.preventDefault());

    // Previene combinaciones de teclas como F12, Ctrl+Shift+I/J/C o Ctrl+U
    document.addEventListener("keydown", e => {
        if (
            e.key === "F12" ||
            (e.ctrlKey && e.shiftKey && ["i", "j", "c"].includes(e.key.toLowerCase())) ||
            (e.ctrlKey && e.key.toLowerCase() === "u")
        ) {
            e.preventDefault(); // Cancela la acción sospechosa
            window.location.href = redirectUrl; // Redirige al usuario
        }
    });
}

// Ejecuta las funciones al cargar la página
document.addEventListener("DOMContentLoaded", () => {
    prevenirScraping(); // Activa la protección al cargar

    // También puedes iniciar aquí cualquier otra funcionalidad si es necesario
});
