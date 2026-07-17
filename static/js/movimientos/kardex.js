const kardexArea = document.querySelector("[data-kardex-area]");
const kardexType = document.querySelector("[data-kardex-type]");
const kardexCategory = document.querySelector("[data-kardex-category]");
const kardexProduct = document.querySelector("[data-kardex-product]");
const correctionDialog = document.querySelector("[data-kardex-correction-dialog]");
const correctionForm = document.querySelector("[data-kardex-correction-form]");
const correctionProduct = document.querySelector("[data-kardex-correction-product]");
const correctionQuantity = document.querySelector("[data-kardex-correction-quantity]");
const correctionHelp = document.querySelector("[data-kardex-correction-help]");

function toNumber(value) {
  const number = Number.parseFloat(String(value || "0").replace(",", "."));
  return Number.isFinite(number) ? number : 0;
}

function formatQuantity(value) {
  return Number(value || 0).toLocaleString("es-PE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3,
  });
}

function formatInputQuantity(value) {
  return String(Math.round(toNumber(value) * 1000) / 1000)
    .replace(/(\.\d*?)0+$/, "$1")
    .replace(/\.$/, "");
}

function syncKardexFilterOptions() {
  if (!kardexArea || !kardexType || !kardexCategory || !kardexProduct) return;

  const area = kardexArea.value;

  Array.from(kardexType.options).forEach((option) => {
    if (!option.value) return;
    const visible = !area || option.dataset.area === area;
    option.hidden = !visible;
    option.disabled = !visible;
  });
  if (kardexType.selectedOptions[0]?.disabled) kardexType.value = "";

  const selectedType = kardexType.value;
  Array.from(kardexCategory.options).forEach((option) => {
    if (!option.value) return;
    const visible = (!area || option.dataset.area === area)
      && (!selectedType || option.dataset.type === selectedType);
    option.hidden = !visible;
    option.disabled = !visible;
  });
  if (kardexCategory.selectedOptions[0]?.disabled) kardexCategory.value = "";

  const selectedCategory = kardexCategory.value;
  let visibleProducts = 0;
  Array.from(kardexProduct.options).forEach((option) => {
    if (!option.value) return;
    const visible = (!area || option.dataset.area === area)
      && (!selectedType || option.dataset.type === selectedType)
      && (!selectedCategory || option.dataset.category === selectedCategory);
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible) visibleProducts += 1;
  });
  if (kardexProduct.selectedOptions[0]?.disabled) kardexProduct.value = "";

  const placeholder = kardexProduct.querySelector("option[value='']");
  if (placeholder) {
    placeholder.textContent = visibleProducts ? "Todos los productos" : "No hay productos para esos filtros";
  }
  window.refreshScrollSelects?.(document.querySelector(".kardex-filters"));
}

[kardexArea, kardexType, kardexCategory].forEach((control) => {
  control?.addEventListener("change", syncKardexFilterOptions);
});

document.querySelectorAll("[data-correct-kardex-output]").forEach((button) => {
  button.addEventListener("click", () => {
    if (!correctionDialog || !correctionForm) return;
    correctionForm.action = button.dataset.action;
    correctionQuantity.value = formatInputQuantity(button.dataset.current);
    correctionProduct.textContent = button.dataset.product || "Producto seleccionado";
    correctionHelp.textContent = `Actual: ${formatQuantity(button.dataset.current)} ${button.dataset.unit || ""}`;
    correctionDialog.showModal();
    correctionQuantity.focus();
    correctionQuantity.select();
  });
});

document.querySelectorAll("[data-close-kardex-correction]").forEach((button) => {
  button.addEventListener("click", () => {
    if (correctionDialog?.open) correctionDialog.close();
  });
});

syncKardexFilterOptions();
