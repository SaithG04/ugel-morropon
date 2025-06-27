let idUsuarioAEliminar = null;

document.addEventListener("DOMContentLoaded", () => {
  cargarUsuarios();

  // Confirmar eliminación
  document.getElementById("btn-confirmar-eliminar").addEventListener("click", () => {
    if (!idUsuarioAEliminar) return;

    fetch(`/api/usuarios/${idUsuarioAEliminar}`, { method: "DELETE" })
      .then(res => {
        if (!res.ok) throw new Error("Error al eliminar usuario");
        return res.json();
      })
      .then(() => {
        const modal = bootstrap.Modal.getInstance(document.getElementById("confirmarEliminacionModal"));
        modal.hide();
        mostrarToast("✅ Usuario eliminado correctamente.");
        cargarUsuarios();
      })
      .catch(err => console.error("❌ Error al eliminar:", err));
  });

  // Enviar formulario de edición
  document.body.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "formEditarUsuario") {
      e.preventDefault();

      const form = e.target;
      const formData = new FormData(form);
      const data = Object.fromEntries(formData.entries());

      fetch("/actualizar_usuario", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
        .then(res => {
          if (!res.ok) throw new Error("Error al actualizar");
          return res.json();
        })
        .then(resp => {
          if (resp.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById("modalEditarUsuario"));
            modal.hide();
            cargarUsuarios();
            mostrarToast("✅ Usuario actualizado correctamente.");
          }
        })
        .catch(err => {
          console.error("❌ Error al actualizar:", err);
          alert("Hubo un error al actualizar el usuario.");
        });
    }
  });
});

// Cargar usuarios en tabla
function cargarUsuarios() {
  fetch("/api/usuarios")
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById("tabla-usuarios");
      tbody.innerHTML = "";
      data.forEach((usuario, index) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td class="text-center">${index + 1}</td>
          <td>${usuario.nombre}</td>
          <td>${usuario.apellido}</td>
          <td>${usuario.dni}</td>
          <td>${usuario.telefono || ''}</td>
          <td>${usuario.correo_electronico}</td>
          <td>${usuario.institucion || ''}</td>
          <td>${usuario.clave}</td>
          <td class="text-center">
            <button class="btn btn-sm btn-warning me-1" onclick="editarUsuario('${usuario.id}')">
              <i class="bi bi-pencil-square"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="confirmarEliminacion('${usuario.id}')">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        `;
        tbody.appendChild(row);
      });
    })
    .catch(err => console.error("❌ Error al cargar usuarios:", err));
}

// Confirmar eliminación
function confirmarEliminacion(id) {
  idUsuarioAEliminar = id;
  const modal = new bootstrap.Modal(document.getElementById("confirmarEliminacionModal"));
  modal.show();
}

// Cargar y abrir modal de edición
function editarUsuario(id) {
  fetch(`/modal/editar_usuario/${id}`)
    .then(res => {
      if (!res.ok) throw new Error("No se pudo cargar el modal");
      return res.text();
    })
    .then(html => {
      // Crear contenedor si no existe
      let contenedor = document.getElementById("contenedor-modal-edicion");
      if (!contenedor) {
        contenedor = document.createElement("div");
        contenedor.id = "contenedor-modal-edicion";
        document.body.appendChild(contenedor);
      }
      contenedor.innerHTML = html;

      const modal = new bootstrap.Modal(document.getElementById("modalEditarUsuario"));
      modal.show();
    })
    .catch(err => console.error("❌ Error al cargar modal de edición:", err));
}

// Toast reutilizable
function mostrarToast(mensaje) {
  const toast = document.getElementById("toastEliminado");
  toast.querySelector(".toast-body").innerText = mensaje;
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();
}
