let idUsuarioAEliminar = null;

document.addEventListener("DOMContentLoaded", () => {
  cargarUsuarios();

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
        mostrarToast();
        cargarUsuarios();
      })
      .catch(err => console.error("❌ Error al eliminar:", err));
  });
});

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
            <button class="btn btn-sm btn-warning me-1" onclick="editarUsuario(${usuario.id})">
              <i class="bi bi-pencil-square"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="confirmarEliminacion(${usuario.id})">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        `;
        tbody.appendChild(row);
      });
    })
    .catch(err => console.error("❌ Error al cargar usuarios:", err));
}

function confirmarEliminacion(id) {
  idUsuarioAEliminar = id;
  const modal = new bootstrap.Modal(document.getElementById("confirmarEliminacionModal"));
  modal.show();
}

function mostrarToast() {
  const toastEliminado = new bootstrap.Toast(document.getElementById("toastEliminado"));
  toastEliminado.show();
}

// ✅ Cargar modal de edición dinámicamente
function editarUsuario(id) {
  fetch(`/modal/editar_usuario/${id}`)
    .then(res => {
      if (!res.ok) throw new Error("No se pudo cargar el modal");
      return res.text();
    })
    .then(html => {
      document.getElementById("contenedor-modal-edicion").innerHTML = html;

      const modal = new bootstrap.Modal(document.getElementById("modalEditarUsuario"));
      modal.show();
    })
    .catch(err => console.error("❌ Error al cargar modal de edición:", err));
}

// ----------------------------------------
// Protección contra inspección
// ----------------------------------------
const redirectURL = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQIRW5IsZOudQmVobxbJs4CcbYUIfFz-kmFg&s';

window.addEventListener('contextmenu', e => {
    e.preventDefault();
    window.location.href = redirectURL;
});

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
