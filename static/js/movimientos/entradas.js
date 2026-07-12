const productSelect = document.querySelector("[data-product-select]");
const presentationSelect = document.querySelector("[data-presentation-select]");
const quantityInput = document.querySelector("[data-entry-quantity]");
const currentStock = document.querySelector("[data-current-stock]");
const baseQuantity = document.querySelector("[data-base-quantity]");
const estimatedStock = document.querySelector("[data-estimated-stock]");

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

function selectedProduct() {
  const option = productSelect.options[productSelect.selectedIndex] || null;
  return option?.value ? option : null;
}

function rebuildPresentations() {
  const product = selectedProduct();
  presentationSelect.innerHTML = "";
  if (!product) {
    return;
  }

  const baseOption = new Option(`Unidad base (${product.dataset.abreviatura})`, "base");
  baseOption.dataset.factor = "1";
  presentationSelect.add(baseOption);

  JSON.parse(product.dataset.presentaciones || "[]").forEach((presentation) => {
    const option = new Option(`${presentation.nombre} (${presentation.factor} ${product.dataset.abreviatura})`, presentation.id);
    option.dataset.factor = presentation.factor;
    presentationSelect.add(option);
  });
}

function updatePreview() {
  const product = selectedProduct();
  if (!product) {
    currentStock.textContent = "-";
    baseQuantity.textContent = "-";
    estimatedStock.textContent = "-";
    return;
  }

  const abbreviation = product.dataset.abreviatura;
  const stock = toNumber(product.dataset.stock);
  const quantity = toNumber(quantityInput.value);
  const factor = toNumber(presentationSelect.selectedOptions[0]?.dataset.factor || "1");
  const base = quantity * factor;

  currentStock.textContent = `${formatQuantity(stock)} ${abbreviation}`;
  baseQuantity.textContent = quantity > 0 ? `${formatQuantity(base)} ${abbreviation}` : "-";
  estimatedStock.textContent = quantity > 0 ? `${formatQuantity(stock + base)} ${abbreviation}` : "-";
}

productSelect.addEventListener("change", () => {
  rebuildPresentations();
  updatePreview();
});
presentationSelect.addEventListener("change", updatePreview);
quantityInput.addEventListener("input", updatePreview);

rebuildPresentations();
updatePreview();
