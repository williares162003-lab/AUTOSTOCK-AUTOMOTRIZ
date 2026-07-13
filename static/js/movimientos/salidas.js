const vehiclePlate = document.querySelector("[data-vehicle-plate]");
const vehicleModel = document.querySelector("[data-vehicle-model]");
const vehicleList = document.querySelector("#vehiculos-atendidos");
const linesContainer = document.querySelector("[data-output-lines]");
const lineTemplate = document.querySelector("[data-output-line-template]");
const addLineButton = document.querySelector("[data-add-output-line]");

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

function filterCategoriesByType(typeSelect, categorySelect) {
  if (!typeSelect || !categorySelect) return;

  const selectedType = typeSelect.value;
  const currentValue = categorySelect.value;
  let currentVisible = false;
  Array.from(categorySelect.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      option.disabled = true;
      return;
    }

    const visible = selectedType && option.dataset.type === selectedType;
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible && option.value === currentValue) currentVisible = true;
  });

  if (!selectedType || !currentVisible) {
    categorySelect.value = "";
  }
  categorySelect.disabled = !selectedType;
}

function filterProductsBySelection(typeSelect, categorySelect, productSelect) {
  if (!typeSelect || !categorySelect || !productSelect) return;

  const selectedType = typeSelect.value;
  const selectedCategory = categorySelect.value;
  const placeholder = Array.from(productSelect.options).find((option) => !option.value);
  let firstVisible = null;
  Array.from(productSelect.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      option.disabled = true;
      return;
    }

    const visible = selectedType
      && selectedCategory
      && option.dataset.type === selectedType
      && option.dataset.category === selectedCategory;
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible && !firstVisible) firstVisible = option;
  });

  const current = productSelect.options[productSelect.selectedIndex] || null;
  if (!selectedType || !selectedCategory || !firstVisible) {
    if (placeholder) {
      placeholder.textContent = !selectedType
        ? "Primero el tipo"
        : (!selectedCategory ? "Primero categoria" : "No hay productos en esta categoria");
    }
    productSelect.value = "";
    productSelect.disabled = true;
    return;
  }

  if (placeholder) {
    placeholder.textContent = "Selecciona producto";
  }
  productSelect.disabled = false;
  if (!current?.value || current.hidden || current.disabled) {
    productSelect.value = firstVisible.value;
  }
}

function syncProductPicker(typeSelect, categorySelect, productSelect) {
  filterCategoriesByType(typeSelect, categorySelect);
  filterProductsBySelection(typeSelect, categorySelect, productSelect);
}

function syncVehicleModel() {
  const plate = vehiclePlate.value.trim().toUpperCase();
  vehiclePlate.value = plate;
  const option = Array.from(vehicleList.options).find((item) => item.value.toUpperCase() === plate);
  if (option && !vehicleModel.value.trim()) {
    vehicleModel.value = option.dataset.modelo || "";
  }
}

function selectedProduct(row) {
  const select = row.querySelector("[data-line-product]");
  const option = select.options[select.selectedIndex] || null;
  return option?.value ? option : null;
}

function updateLine(row) {
  const product = selectedProduct(row);
  const origin = row.querySelector("[data-line-origin]");
  const quantity = row.querySelector("[data-line-quantity]");
  const stock = row.querySelector("[data-line-stock]");
  if (!product) {
    stock.textContent = "-";
    return;
  }

  const originValue = origin.value;
  const abbreviation = product.dataset.abreviatura;
  const allowsDecimal = product.dataset.decimal === "1";
  quantity.step = allowsDecimal ? "0.001" : "1";
  quantity.min = allowsDecimal ? "0.001" : "1";
  if (originValue === "balde_abierto") {
    const openBuckets = toNumber(product.dataset.baldesAbiertos);
    const used = toNumber(product.dataset.stockBaldeAbierto);
    quantity.removeAttribute("max");
    stock.textContent = openBuckets > 0
      ? `${formatQuantity(openBuckets)} balde(s) / usado ${formatQuantity(used)} ${abbreviation}`
      : "Sin balde abierto";
    return;
  }

  if (originValue === "cilindro_abierto") {
    const openCylinders = toNumber(product.dataset.cilindrosAbiertos);
    const used = toNumber(product.dataset.stockCilindroAbierto);
    const capacity = toNumber(product.dataset.litrosPorCilindro);
    const available = Math.max(capacity - used, 0);
    quantity.max = String(available);
    stock.textContent = openCylinders > 0
      ? `${formatQuantity(openCylinders)} cilindro(s) / queda ${formatQuantity(available)} ${abbreviation}`
      : "Sin cilindro abierto";
    return;
  }

  const available = toNumber(product.dataset.stockSuelto);
  quantity.max = String(available);
  stock.textContent = `${formatQuantity(available)} ${abbreviation}`;
}

function addLine() {
  const fragment = lineTemplate.content.cloneNode(true);
  const row = fragment.querySelector("[data-output-line]");
  const typeSelect = row.querySelector("[data-line-type]");
  const categorySelect = row.querySelector("[data-line-category]");
  const productSelect = row.querySelector("[data-line-product]");
  typeSelect.addEventListener("change", () => {
    syncProductPicker(typeSelect, categorySelect, productSelect);
    updateLine(row);
  });
  categorySelect.addEventListener("change", () => {
    syncProductPicker(typeSelect, categorySelect, productSelect);
    updateLine(row);
  });
  productSelect.addEventListener("change", () => updateLine(row));
  row.querySelector("[data-line-origin]").addEventListener("change", () => updateLine(row));
  row.querySelector("[data-remove-line]").addEventListener("click", () => {
    if (linesContainer.children.length > 1) row.remove();
  });
  linesContainer.appendChild(row);
  syncProductPicker(typeSelect, categorySelect, productSelect);
  updateLine(row);
}

vehiclePlate.addEventListener("change", syncVehicleModel);
vehiclePlate.addEventListener("blur", syncVehicleModel);
addLineButton.addEventListener("click", addLine);

addLine();
