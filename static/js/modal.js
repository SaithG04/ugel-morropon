document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('formEditarUsuario');
  const toastElement = document.getElementById('toastEliminado');
  const toastBody = toastElement.querySelector('.toast-body');
  const toast = new bootstrap.Toast(toastElement);

  if (!form) {
    console.warn("⚠️ No se encontró el formulario 'formEditarUsuario'.");
    return;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault(); // Evita envío tradicional (por URL)

    const formData = new FormData(form);

    try {
      const response = await fetch('/actualizar_usuario', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        toastBody.textContent = "✅ Usuario actualizado correctamente.";
        toastElement.classList.remove("bg-danger");
        toastElement.classList.add("bg-success");
        toast.show();

        // Opcional: cerrar modal y refrescar tabla después de un segundo
        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarUsuario'));
          modal.hide();
          location.reload();
        }, 1500);
      } else {
        toastBody.textContent = "❌ Error al actualizar el usuario.";
        toastElement.classList.remove("bg-success");
        toastElement.classList.add("bg-danger");
        toast.show();
      }

    } catch (error) {
      console.error("❌ Error en fetch:", error);
      toastBody.textContent = "⚠️ Error en la solicitud al servidor.";
      toastElement.classList.remove("bg-success");
      toastElement.classList.add("bg-danger");
      toast.show();
    }
  });
});
