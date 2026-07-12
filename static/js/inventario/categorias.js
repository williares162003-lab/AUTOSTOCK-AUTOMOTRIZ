const categoryDialog = document.querySelector("[data-category-dialog]");
const categoryForm = document.querySelector("[data-category-form]");
const typeDialog = document.querySelector("[data-type-dialog]");
const typeForm = document.querySelector("[data-type-form]");

document.querySelector("[data-open-type]").addEventListener("click", () => {
  typeForm.reset();
  typeForm.action = window.typeCreateUrl;
  document.querySelector("[data-type-title]").textContent = "Nuevo tipo";
  typeDialog.showModal();
});

document.querySelectorAll("[data-edit-type]").forEach((button) => {
  button.addEventListener("click", () => {
    typeForm.action = button.dataset.action;
    typeForm.elements.nombre.value = button.dataset.nombre;
    document.querySelector("[data-type-title]").textContent = "Editar tipo";
    typeDialog.showModal();
  });
});

document.querySelector("[data-open-category]").addEventListener("click", () => {
  categoryForm.reset();
  categoryForm.action = window.categoryCreateUrl;
  document.querySelector("[data-category-title]").textContent = "Nueva categoria";
  categoryDialog.showModal();
});

document.querySelectorAll("[data-edit-category]").forEach((button) => {
  button.addEventListener("click", () => {
    categoryForm.action = button.dataset.action;
    categoryForm.elements.nombre.value = button.dataset.nombre;
    categoryForm.elements.tipo_id.value = button.dataset.tipoId;
    document.querySelector("[data-category-title]").textContent = "Editar categoria";
    categoryDialog.showModal();
  });
});

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

const typeFilter = document.querySelector("[data-category-type-filter]");
const categoryItems = Array.from(document.querySelectorAll("[data-category-item]"));
typeFilter.addEventListener("change", () => {
  categoryItems.forEach((item) => {
    item.hidden = Boolean(typeFilter.value) && item.dataset.type !== typeFilter.value;
  });
});

document.querySelectorAll("[data-delete-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(`¿Eliminar la categoria ${form.dataset.name}?`)) event.preventDefault();
  });
});

document.querySelectorAll("[data-delete-type]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(`¿Eliminar el tipo ${form.dataset.name}?`)) event.preventDefault();
  });
});
