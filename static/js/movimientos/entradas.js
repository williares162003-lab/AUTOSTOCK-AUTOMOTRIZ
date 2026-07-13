const entryType = document.querySelector("[data-entry-type]");
const entryProductArea = document.querySelector("[data-entry-product-area]");
const entryProductType = document.querySelector("[data-entry-product-type]");
const entryProductCategory = document.querySelector("[data-entry-product-category]");
const productSelect = document.querySelector("[data-product-select]");
const presentationField = document.querySelector("[data-presentation-field]");
const presentationSelect = document.querySelector("[data-presentation-select]");
const quantityInput = document.querySelector("[data-entry-quantity]");
const cylinderLitersField = document.querySelector("[data-cylinder-liters-field]");
const cylinderLitersInput = document.querySelector("[data-cylinder-liters]");
const quantityLabel = document.querySelector("[data-quantity-label]");
const currentLabel = document.querySelector("[data-current-label]");
const entryLabel = document.querySelector("[data-entry-label]");
const estimatedLabel = document.querySelector("[data-estimated-label]");
const currentStock = document.querySelector("[data-current-stock]");
const baseQuantity = document.querySelector("[data-base-quantity]");
const estimatedStock = document.querySelector("[data-estimated-stock]");

const bucketProductType = document.querySelector("[data-bucket-product-type]");
const bucketProductArea = document.querySelector("[data-bucket-product-area]");
const bucketProductCategory = document.querySelector("[data-bucket-product-category]");
const bucketProduct = document.querySelector("[data-bucket-product]");
const bucketCloseProductType = document.querySelector("[data-bucket-close-product-type]");
const bucketCloseProductArea = document.querySelector("[data-bucket-close-product-area]");
const bucketCloseProductCategory = document.querySelector("[data-bucket-close-product-category]");
const bucketCloseProduct = document.querySelector("[data-bucket-close-product]");
const bucketClosed = document.querySelector("[data-bucket-closed]");
const bucketOpen = document.querySelector("[data-bucket-open]");
const bucketUsed = document.querySelector("[data-bucket-used]");
const closeOpen = document.querySelector("[data-close-open]");
const closeUsed = document.querySelector("[data-close-used]");
const cylinderProductType = document.querySelector("[data-cylinder-product-type]");
const cylinderProductArea = document.querySelector("[data-cylinder-product-area]");
const cylinderProductCategory = document.querySelector("[data-cylinder-product-category]");
const cylinderProduct = document.querySelector("[data-cylinder-product]");
const cylinderCloseProductType = document.querySelector("[data-cylinder-close-product-type]");
const cylinderCloseProductArea = document.querySelector("[data-cylinder-close-product-area]");
const cylinderCloseProductCategory = document.querySelector("[data-cylinder-close-product-category]");
const cylinderCloseProduct = document.querySelector("[data-cylinder-close-product]");
const cylinderClosed = document.querySelector("[data-cylinder-closed]");
const cylinderOpen = document.querySelector("[data-cylinder-open]");
const cylinderCapacity = document.querySelector("[data-cylinder-capacity]");
const cylinderUsed = document.querySelector("[data-cylinder-used]");
const cylinderCloseOpen = document.querySelector("[data-cylinder-close-open]");
const cylinderCloseUsed = document.querySelector("[data-cylinder-close-used]");
const cylinderCloseLeft = document.querySelector("[data-cylinder-close-left]");

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

function filterTypesByArea(areaSelect, typeSelect) {
  if (!areaSelect || !typeSelect) return;

  const selectedArea = areaSelect.value;
  const currentValue = typeSelect.value;
  let currentVisible = false;
  Array.from(typeSelect.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      option.disabled = true;
      option.textContent = selectedArea ? "Selecciona un tipo" : "Primero selecciona un area";
      return;
    }

    const visible = selectedArea && option.dataset.area === selectedArea;
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible && option.value === currentValue) currentVisible = true;
  });

  if (!selectedArea || !currentVisible) {
    typeSelect.value = "";
  }
  typeSelect.disabled = !selectedArea;
}

function filterCategoriesBySelection(areaSelect, typeSelect, categorySelect) {
  if (!areaSelect || !typeSelect || !categorySelect) return;

  const selectedArea = areaSelect.value;
  const selectedType = typeSelect.value;
  const currentValue = categorySelect.value;
  let currentVisible = false;
  Array.from(categorySelect.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      option.disabled = true;
      option.textContent = !selectedArea
        ? "Primero selecciona un area"
        : (!selectedType ? "Primero selecciona un tipo" : "Selecciona una categoria");
      return;
    }

    const visible = selectedArea
      && selectedType
      && option.dataset.area === selectedArea
      && option.dataset.type === selectedType;
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible && option.value === currentValue) currentVisible = true;
  });

  if (!selectedArea || !selectedType || !currentVisible) {
    categorySelect.value = "";
  }
  categorySelect.disabled = !selectedArea || !selectedType;
}

function filterProductsBySelection(areaSelect, typeSelect, categorySelect, select) {
  if (!areaSelect || !typeSelect || !categorySelect || !select) return;

  const selectedArea = areaSelect.value;
  const selectedType = typeSelect.value;
  const selectedCategory = categorySelect.value;
  const placeholder = Array.from(select.options).find((option) => !option.value);
  let firstVisible = null;
  Array.from(select.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      option.disabled = true;
      return;
    }

    const visible = selectedArea
      && selectedType
      && selectedCategory
      && option.dataset.area === selectedArea
      && option.dataset.type === selectedType
      && option.dataset.category === selectedCategory;
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible && !firstVisible) firstVisible = option;
  });

  const current = select.options[select.selectedIndex] || null;
  if (!selectedArea || !selectedType || !selectedCategory || !firstVisible) {
    if (placeholder) {
      placeholder.textContent = !selectedArea
        ? "Primero selecciona un area"
        : (!selectedType
          ? "Primero selecciona un tipo"
          : (!selectedCategory ? "Primero selecciona una categoria" : "No hay productos en esta categoria"));
    }
    select.value = "";
    select.disabled = true;
    return;
  }

  if (placeholder) {
    placeholder.textContent = "Selecciona un producto";
  }
  select.disabled = false;
  if (!current?.value || current.hidden || current.disabled) {
    select.value = firstVisible.value;
  }
}

function syncProductPicker(areaSelect, typeSelect, categorySelect, select) {
  filterTypesByArea(areaSelect, typeSelect);
  filterCategoriesBySelection(areaSelect, typeSelect, categorySelect);
  filterProductsBySelection(areaSelect, typeSelect, categorySelect, select);
}

function toggleField(field, isHidden) {
  if (!field) return;
  field.hidden = isHidden;
  field.style.display = isHidden ? "none" : "";
}

function selectedProduct() {
  const option = productSelect.options[productSelect.selectedIndex] || null;
  return option?.value ? option : null;
}

function selectedBucketProduct() {
  const option = bucketProduct?.options[bucketProduct.selectedIndex] || null;
  return option?.value ? option : null;
}

function selectedBucketCloseProduct() {
  const option = bucketCloseProduct?.options[bucketCloseProduct.selectedIndex] || null;
  return option?.value ? option : null;
}

function selectedCylinderProduct() {
  const option = cylinderProduct?.options[cylinderProduct.selectedIndex] || null;
  return option?.value ? option : null;
}

function selectedCylinderCloseProduct() {
  const option = cylinderCloseProduct?.options[cylinderCloseProduct.selectedIndex] || null;
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
  const isCylinder = entryType.value === "cilindro_cerrado";
  toggleField(presentationField, isBucket || isCylinder);
  presentationSelect.disabled = isBucket || isCylinder;
  toggleField(cylinderLitersField, !isCylinder);
  cylinderLitersInput.disabled = !isCylinder;
  quantityInput.step = isBucket || isCylinder ? "1" : "0.001";
  quantityInput.min = isBucket || isCylinder ? "1" : "0.001";
  quantityLabel.textContent = isBucket ? "Cantidad de baldes" : (isCylinder ? "Cantidad de cilindros" : "Cantidad que ingresa");
  currentLabel.textContent = isBucket ? "Baldes cerrados" : (isCylinder ? "Cilindros cerrados" : "Stock disponible");
  entryLabel.textContent = isBucket ? "Entrada de baldes" : (isCylinder ? "Entrada de cilindros" : "Entrada al stock");
  estimatedLabel.textContent = isBucket ? "Baldes estimados" : (isCylinder ? "Cilindros estimados" : "Stock estimado");
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
  const isCylinder = entryType.value === "cilindro_cerrado";
  const abbreviation = product.dataset.abreviatura;
  const quantity = toNumber(quantityInput.value);

  if (isBucket) {
    const closedBuckets = toNumber(product.dataset.stockBaldesCerrados);
    currentStock.textContent = `${formatQuantity(closedBuckets)} balde(s)`;
    baseQuantity.textContent = quantity > 0 ? `${formatQuantity(quantity)} balde(s)` : "-";
    estimatedStock.textContent = quantity > 0 ? `${formatQuantity(closedBuckets + quantity)} balde(s)` : "-";
    return;
  }

  if (isCylinder) {
    const closedCylinders = toNumber(product.dataset.stockCilindrosCerrados);
    const liters = toNumber(cylinderLitersInput.value || product.dataset.litrosPorCilindro);
    currentStock.textContent = `${formatQuantity(closedCylinders)} cilindro(s)`;
    baseQuantity.textContent = quantity > 0
      ? `${formatQuantity(quantity)} cilindro(s) / ${formatQuantity(quantity * liters)} ${abbreviation}`
      : "-";
    estimatedStock.textContent = quantity > 0 ? `${formatQuantity(closedCylinders + quantity)} cilindro(s)` : "-";
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
    bucketOpen.textContent = "-";
    bucketUsed.textContent = "-";
    return;
  }

  const abbreviation = product.dataset.abreviatura;
  const closed = toNumber(product.dataset.stockBaldesCerrados);
  const inUse = toNumber(product.dataset.baldesAbiertos);
  const used = toNumber(product.dataset.stockBaldeAbierto);
  bucketClosed.textContent = `${formatQuantity(closed)} balde(s)`;
  bucketOpen.textContent = `${formatQuantity(inUse)} balde(s)`;
  bucketUsed.textContent = `${formatQuantity(used)} ${abbreviation}`;
}

function updateClosePreview() {
  const product = selectedBucketCloseProduct();
  if (!product) {
    closeOpen.textContent = "-";
    closeUsed.textContent = "-";
    return;
  }

  closeOpen.textContent = `${formatQuantity(product.dataset.baldesAbiertos)} balde(s)`;
  closeUsed.textContent = `${formatQuantity(product.dataset.stockBaldeAbierto)} ${product.dataset.abreviatura}`;
}

function updateCylinderPreview() {
  const product = selectedCylinderProduct();
  if (!product) {
    cylinderClosed.textContent = "-";
    cylinderOpen.textContent = "-";
    cylinderCapacity.textContent = "-";
    cylinderUsed.textContent = "-";
    return;
  }

  const abbreviation = product.dataset.abreviatura;
  const closed = toNumber(product.dataset.stockCilindrosCerrados);
  const inUse = toNumber(product.dataset.cilindrosAbiertos);
  const used = toNumber(product.dataset.stockCilindroAbierto);
  const capacity = toNumber(product.dataset.litrosPorCilindro);
  cylinderClosed.textContent = `${formatQuantity(closed)} cilindro(s)`;
  cylinderOpen.textContent = `${formatQuantity(inUse)} cilindro(s)`;
  cylinderCapacity.textContent = `${formatQuantity(capacity)} ${abbreviation}`;
  cylinderUsed.textContent = `${formatQuantity(used)} ${abbreviation}`;
}

function updateCylinderClosePreview() {
  const product = selectedCylinderCloseProduct();
  if (!product) {
    cylinderCloseOpen.textContent = "-";
    cylinderCloseUsed.textContent = "-";
    cylinderCloseLeft.textContent = "-";
    return;
  }

  const used = toNumber(product.dataset.stockCilindroAbierto);
  const capacity = toNumber(product.dataset.litrosPorCilindro);
  const left = Math.max(capacity - used, 0);
  cylinderCloseOpen.textContent = `${formatQuantity(product.dataset.cilindrosAbiertos)} cilindro(s)`;
  cylinderCloseUsed.textContent = `${formatQuantity(used)} ${product.dataset.abreviatura}`;
  cylinderCloseLeft.textContent = `${formatQuantity(left)} ${product.dataset.abreviatura}`;
}

function refreshEntry() {
  syncProductPicker(entryProductArea, entryProductType, entryProductCategory, productSelect);
  rebuildPresentations();
  syncEntryMode();
  updatePreview();
}

entryType.addEventListener("change", refreshEntry);
entryProductArea.addEventListener("change", refreshEntry);
entryProductType.addEventListener("change", refreshEntry);
entryProductCategory.addEventListener("change", refreshEntry);
productSelect.addEventListener("change", () => {
  rebuildPresentations();
  updatePreview();
});
presentationSelect.addEventListener("change", updatePreview);
quantityInput.addEventListener("input", updatePreview);
cylinderLitersInput.addEventListener("input", updatePreview);

if (bucketProduct) {
  bucketProductArea.addEventListener("change", () => {
    syncProductPicker(bucketProductArea, bucketProductType, bucketProductCategory, bucketProduct);
    updateBucketPreview();
  });
  bucketProductType.addEventListener("change", () => {
    syncProductPicker(bucketProductArea, bucketProductType, bucketProductCategory, bucketProduct);
    updateBucketPreview();
  });
  bucketProductCategory.addEventListener("change", () => {
    syncProductPicker(bucketProductArea, bucketProductType, bucketProductCategory, bucketProduct);
    updateBucketPreview();
  });
  syncProductPicker(bucketProductArea, bucketProductType, bucketProductCategory, bucketProduct);
  bucketProduct.addEventListener("change", updateBucketPreview);
  updateBucketPreview();
}

if (bucketCloseProduct) {
  bucketCloseProductArea.addEventListener("change", () => {
    syncProductPicker(bucketCloseProductArea, bucketCloseProductType, bucketCloseProductCategory, bucketCloseProduct);
    updateClosePreview();
  });
  bucketCloseProductType.addEventListener("change", () => {
    syncProductPicker(bucketCloseProductArea, bucketCloseProductType, bucketCloseProductCategory, bucketCloseProduct);
    updateClosePreview();
  });
  bucketCloseProductCategory.addEventListener("change", () => {
    syncProductPicker(bucketCloseProductArea, bucketCloseProductType, bucketCloseProductCategory, bucketCloseProduct);
    updateClosePreview();
  });
  syncProductPicker(bucketCloseProductArea, bucketCloseProductType, bucketCloseProductCategory, bucketCloseProduct);
  bucketCloseProduct.addEventListener("change", updateClosePreview);
  updateClosePreview();
}

if (cylinderProduct) {
  cylinderProductArea.addEventListener("change", () => {
    syncProductPicker(cylinderProductArea, cylinderProductType, cylinderProductCategory, cylinderProduct);
    updateCylinderPreview();
  });
  cylinderProductType.addEventListener("change", () => {
    syncProductPicker(cylinderProductArea, cylinderProductType, cylinderProductCategory, cylinderProduct);
    updateCylinderPreview();
  });
  cylinderProductCategory.addEventListener("change", () => {
    syncProductPicker(cylinderProductArea, cylinderProductType, cylinderProductCategory, cylinderProduct);
    updateCylinderPreview();
  });
  syncProductPicker(cylinderProductArea, cylinderProductType, cylinderProductCategory, cylinderProduct);
  cylinderProduct.addEventListener("change", updateCylinderPreview);
  updateCylinderPreview();
}

if (cylinderCloseProduct) {
  cylinderCloseProductArea.addEventListener("change", () => {
    syncProductPicker(cylinderCloseProductArea, cylinderCloseProductType, cylinderCloseProductCategory, cylinderCloseProduct);
    updateCylinderClosePreview();
  });
  cylinderCloseProductType.addEventListener("change", () => {
    syncProductPicker(cylinderCloseProductArea, cylinderCloseProductType, cylinderCloseProductCategory, cylinderCloseProduct);
    updateCylinderClosePreview();
  });
  cylinderCloseProductCategory.addEventListener("change", () => {
    syncProductPicker(cylinderCloseProductArea, cylinderCloseProductType, cylinderCloseProductCategory, cylinderCloseProduct);
    updateCylinderClosePreview();
  });
  syncProductPicker(cylinderCloseProductArea, cylinderCloseProductType, cylinderCloseProductCategory, cylinderCloseProduct);
  cylinderCloseProduct.addEventListener("change", updateCylinderClosePreview);
  updateCylinderClosePreview();
}

refreshEntry();
