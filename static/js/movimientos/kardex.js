const kardexArea = document.querySelector("[data-kardex-area]");
const kardexType = document.querySelector("[data-kardex-type]");
const kardexCategory = document.querySelector("[data-kardex-category]");
const kardexProduct = document.querySelector("[data-kardex-product]");

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

syncKardexFilterOptions();
