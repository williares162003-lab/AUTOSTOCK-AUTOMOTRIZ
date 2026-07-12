const entryType = document.querySelector("[data-entry-type]");
const productSelect = document.querySelector("[data-product-select]");
const presentationField = document.querySelector("[data-presentation-field]");
const presentationSelect = document.querySelector("[data-presentation-select]");
const quantityInput = document.querySelector("[data-entry-quantity]");
const quantityLabel = document.querySelector("[data-quantity-label]");
const currentLabel = document.querySelector("[data-current-label]");
const entryLabel = document.querySelector("[data-entry-label]");
const estimatedLabel = document.querySelector("[data-estimated-label]");
const currentStock = document.querySelector("[data-current-stock]");
const baseQuantity = document.querySelector("[data-base-quantity]");
const estimatedStock = document.querySelector("[data-estimated-stock]");

const bucketProduct = document.querySelector("[data-bucket-product]");
const bucketCount = document.querySelector("[data-bucket-count]");
const bucketContent = document.querySelector("[data-bucket-content]");
const bucketClosed = document.querySelector("[data-bucket-closed]");
const bucketAdded = document.querySelector("[data-bucket-added]");
const bucketOpen = document.querySelector("[data-bucket-open]");

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

function selectedBucketProduct() {
  const option = bucketProduct?.options[bucketProduct.selectedIndex] || null;
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
    const option = new Option(
      `${presentation.nombre} (${presentation.factor} ${product.dataset.abreviatura})`,
      presentation.id
    );
    option.dataset.factor = presentation.factor;
    presentationSelect.add(option);
  });
}

function syncEntryMode() {
  const isBucket = entryType.value === "balde_cerrado";
  presentationField.hidden = isBucket;
  presentationSelect.disabled = isBucket;
  quantityInput.step = isBucket ? "1" : "0.001";
  quantityInput.min = isBucket ? "1" : "0.001";
  quantityLabel.textContent = isBucket ? "Cantidad de baldes" : "Cantidad que ingresa";
  currentLabel.textContent = isBucket ? "Baldes cerrados" : "Stock disponible";
  entryLabel.textContent = isBucket ? "Entrada de baldes" : "Entrada al stock";
  estimatedLabel.textContent = isBucket ? "Baldes estimados" : "Stock estimado";
}

function updatePreview() {
  const product = selectedProduct();
  if (!product) {
    currentStock.textContent = "-";
    baseQuantity.textContent = "-";
    estimatedStock.textContent = "-";
    return;
  }

  const isBucket = entryType.value === "balde_cerrado";
  const abbreviation = product.dataset.abreviatura;
  const quantity = toNumber(quantityInput.value);

  if (isBucket) {
    const closedBuckets = toNumber(product.dataset.stockBaldesCerrados);
    currentStock.textContent = `${formatQuantity(closedBuckets)} balde(s)`;
    baseQuantity.textContent = quantity > 0 ? `${formatQuantity(quantity)} balde(s)` : "-";
    estimatedStock.textContent = quantity > 0 ? `${formatQuantity(closedBuckets + quantity)} balde(s)` : "-";
    return;
  }

  const stock = toNumber(product.dataset.stock);
  const factor = toNumber(presentationSelect.selectedOptions[0]?.dataset.factor || "1");
  const base = quantity * factor;

  currentStock.textContent = `${formatQuantity(stock)} ${abbreviation}`;
  baseQuantity.textContent = quantity > 0 ? `${formatQuantity(base)} ${abbreviation}` : "-";
  estimatedStock.textContent = quantity > 0 ? `${formatQuantity(stock + base)} ${abbreviation}` : "-";
}

function updateBucketPreview() {
  const product = selectedBucketProduct();
  if (!product) {
    bucketClosed.textContent = "-";
    bucketAdded.textContent = "-";
    bucketOpen.textContent = "-";
    return;
  }

  const abbreviation = product.dataset.abreviatura;
  const closed = toNumber(product.dataset.stockBaldesCerrados);
  const opened = toNumber(product.dataset.stockBaldeAbierto);
  const count = toNumber(bucketCount.value);
  const content = toNumber(bucketContent.value);
  const added = count * content;

  bucketCount.max = String(closed);
  bucketClosed.textContent = `${formatQuantity(closed)} balde(s)`;
  bucketAdded.textContent = added > 0 ? `${formatQuantity(added)} ${abbreviation}` : "-";
  bucketOpen.textContent = added > 0 ? `${formatQuantity(opened + added)} ${abbreviation}` : `${formatQuantity(opened)} ${abbreviation}`;
}

function refreshEntry() {
  syncEntryMode();
  updatePreview();
}

entryType.addEventListener("change", refreshEntry);
productSelect.addEventListener("change", () => {
  rebuildPresentations();
  updatePreview();
});
presentationSelect.addEventListener("change", updatePreview);
quantityInput.addEventListener("input", updatePreview);

if (bucketProduct) {
  bucketProduct.addEventListener("change", updateBucketPreview);
  bucketCount.addEventListener("input", updateBucketPreview);
  bucketContent.addEventListener("input", updateBucketPreview);
  updateBucketPreview();
}

rebuildPresentations();
refreshEntry();
