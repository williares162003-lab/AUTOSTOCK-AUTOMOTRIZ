const categoryDialog = document.querySelector("[data-category-dialog]");
const categoryTargetArea = document.querySelector("[data-category-target-area]");
const categoryTargetType = document.querySelector("[data-category-target-type]");
const existingCategory = document.querySelector("[data-existing-category]");
const existingCategoryForm = document.querySelector("[data-existing-category-form]");
const newCategoryForm = document.querySelector("[data-new-category-form]");
const typeDialog = document.querySelector("[data-type-dialog]");
const typeForm = document.querySelector("[data-type-form]");

function updateTargetTypes() {
  const areaId = categoryTargetArea.value;
  let firstAvailable = null;
  Array.from(categoryTargetType.options).forEach((option) => {
    const available = option.dataset.area === areaId;
    option.hidden = !available;
    option.disabled = !available;
    if (available && !firstAvailable) firstAvailable = option;
  });
  const current = categoryTargetType.options[categoryTargetType.selectedIndex];
  if (!current || current.hidden || current.disabled) {
    categoryTargetType.value = firstAvailable?.value || "";
  }
  categoryTargetType.disabled = !firstAvailable;
}

function updateCategoryOptions() {
  updateTargetTypes();
  const areaId = categoryTargetArea.value;
  const typeId = categoryTargetType.value;
  let firstAvailable = null;

  document.querySelectorAll("[data-category-area-input]").forEach((input) => {
    input.value = areaId;
  });
  document.querySelectorAll("[data-category-type-input]").forEach((input) => {
    input.value = typeId;
  });

  Array.from(existingCategory.options).forEach((option) => {
    const assignedTypes = option.dataset.tipos.split(",");
    const available = !assignedTypes.includes(typeId);
    option.hidden = !available;
    option.disabled = !available;
    if (available && !firstAvailable) firstAvailable = option;
  });

  existingCategory.value = firstAvailable?.value || "";
  existingCategory.disabled = !firstAvailable;
  existingCategoryForm.querySelector("[data-add-existing]").disabled = !firstAvailable;
  document.querySelector("[data-no-existing]").hidden = Boolean(firstAvailable);
}

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
    typeForm.elements.area_id.value = button.dataset.areaId;
    document.querySelector("[data-type-title]").textContent = "Editar tipo";
    typeDialog.showModal();
  });
});

document.querySelector("[data-open-category]").addEventListener("click", () => {
  newCategoryForm.reset();
  updateCategoryOptions();
  categoryDialog.showModal();
});

categoryTargetArea.addEventListener("change", updateCategoryOptions);
categoryTargetType.addEventListener("change", updateCategoryOptions);

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

document.querySelectorAll("[data-delete-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(`Eliminar la categoria ${form.dataset.name}?`)) event.preventDefault();
  });
});

document.querySelectorAll("[data-delete-type]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(`Eliminar el tipo ${form.dataset.name}?`)) event.preventDefault();
  });
});
