const categoryDialog = document.querySelector("[data-category-dialog]");
const categoryForm = document.querySelector("[data-category-form]");

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
