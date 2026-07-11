const userRows = Array.from(document.querySelectorAll("[data-user-row]"));
const searchInput = document.querySelector("[data-user-search]");
const roleFilter = document.querySelector("[data-role-filter]");
const statusFilter = document.querySelector("[data-status-filter]");
const resultCount = document.querySelector("[data-result-count]");
const emptyResult = document.querySelector("[data-filter-empty]");

function filterUsers() {
  const search = searchInput.value.trim().toLowerCase();
  const role = roleFilter.value;
  const status = statusFilter.value;
  let visible = 0;

  userRows.forEach((row) => {
    const matches =
      row.dataset.search.includes(search) &&
      (!role || row.dataset.role === role) &&
      (!status || row.dataset.status === status);
    row.hidden = !matches;
    if (matches) visible += 1;
  });

  resultCount.textContent = String(visible);
  emptyResult.hidden = visible !== 0;
}

[searchInput, roleFilter, statusFilter].forEach((control) => {
  control.addEventListener("input", filterUsers);
});

document.querySelector("[data-open-create]").addEventListener("click", () => {
  document.querySelector("[data-create-dialog]").showModal();
});

document.querySelectorAll("[data-edit-user]").forEach((button) => {
  button.addEventListener("click", () => {
    const dialog = document.querySelector("[data-edit-dialog]");
    const form = dialog.querySelector("[data-edit-form]");
    form.action = button.dataset.action;
    ["usuario", "nombre", "correo", "documento", "rol", "estado"].forEach((field) => {
      form.elements[field].value = button.dataset[field];
    });
    dialog.showModal();
  });
});

document.querySelectorAll("[data-password-user]").forEach((button) => {
  button.addEventListener("click", () => {
    const dialog = document.querySelector("[data-password-dialog]");
    const form = dialog.querySelector("[data-password-form]");
    form.action = button.dataset.action;
    form.reset();
    dialog.querySelector("[data-password-name]").textContent = button.dataset.nombre;
    dialog.showModal();
  });
});

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

document.querySelectorAll("[data-state-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const action = form.dataset.nextState === "activo" ? "activar" : "suspender";
    if (!window.confirm(`¿Deseas ${action} a ${form.dataset.userName}?`)) {
      event.preventDefault();
    }
  });
});

document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
});
