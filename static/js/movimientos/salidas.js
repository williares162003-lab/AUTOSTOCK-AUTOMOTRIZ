const vehiclePlate = document.querySelector("[data-vehicle-plate]");
const vehicleModel = document.querySelector("[data-vehicle-model]");
const vehicleList = document.querySelector("#vehiculos-atendidos");
const linesContainer = document.querySelector("[data-output-lines]");
const lineTemplate = document.querySelector("[data-output-line-template]");
const addLineButton = document.querySelector("[data-add-output-line]");
const cancelOutputForms = document.querySelectorAll("[data-cancel-output-form]");
const correctionDialog = document.querySelector("[data-output-correction-dialog]");
const correctionForm = document.querySelector("[data-output-correction-form]");
const correctionProduct = document.querySelector("[data-output-correction-product]");
const correctionQuantity = document.querySelector("[data-output-correction-quantity]");
const correctionHelp = document.querySelector("[data-output-correction-help]");

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

function filterTypesByArea(areaSelect, typeSelect) {
  if (!areaSelect || !typeSelect) return;

  const selectedArea = areaSelect.value;
  const currentValue = typeSelect.value;
  let currentVisible = false;
  Array.from(typeSelect.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      option.disabled = true;
      option.textContent = selectedArea ? "Selecciona" : "Primero area";
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
        ? "Primero area"
        : (!selectedType ? "Primero el tipo" : "Selecciona categoria");
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

function filterProductsBySelection(areaSelect, typeSelect, categorySelect, productSelect) {
  if (!areaSelect || !typeSelect || !categorySelect || !productSelect) return;

  const selectedArea = areaSelect.value;
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

  const current = productSelect.options[productSelect.selectedIndex] || null;
  if (!selectedArea || !selectedType || !selectedCategory || !firstVisible) {
    if (placeholder) {
      placeholder.textContent = !selectedArea
        ? "Primero area"
        : (!selectedType
          ? "Primero el tipo"
          : (!selectedCategory ? "Primero categoria" : "No hay productos en esta categoria"));
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

function syncProductPicker(areaSelect, typeSelect, categorySelect, productSelect) {
  filterTypesByArea(areaSelect, typeSelect);
  filterCategoriesBySelection(areaSelect, typeSelect, categorySelect);
  filterProductsBySelection(areaSelect, typeSelect, categorySelect, productSelect);
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

function isGallonProduct(product) {
  return String(product?.dataset.abreviatura || "").toLowerCase().includes("gal");
}

function displayAbbreviation(product) {
  return isGallonProduct(product) ? "L" : product.dataset.abreviatura;
}

function gallonLiters(product) {
  return toNumber(product?.dataset.litrosPorGalon);
}

function formatStockForProduct(value, product) {
  const quantity = formatQuantity(value);
  const abbreviation = displayAbbreviation(product);
  if (!isGallonProduct(product)) return `${quantity} ${abbreviation}`;

  const liters = gallonLiters(product);
  if (liters <= 0) return `${quantity} L`;
  return `${quantity} L (${formatQuantity(toNumber(value) / liters)} gal)`;
}

function updateGallonShortcuts(row, product) {
  const shortcuts = row.querySelector("[data-gallon-shortcuts]");
  if (!shortcuts) return;
  const liters = gallonLiters(product);
  const visible = isGallonProduct(product) && liters > 0;
  shortcuts.hidden = !visible;
  if (!visible) return;
  shortcuts.querySelectorAll("[data-gallon-fraction]").forEach((button) => {
    const fraction = toNumber(button.dataset.gallonFraction);
    const value = liters * fraction;
    button.title = `${formatQuantity(value)} L`;
  });
}

function cylinderAvailable(product) {
  const savedAvailable = toNumber(product?.dataset.stockCilindroDisponible);
  if (savedAvailable > 0) return savedAvailable;
  const openCylinders = toNumber(product?.dataset.cilindrosAbiertos);
  const used = toNumber(product?.dataset.stockCilindroAbierto);
  const capacity = toNumber(product?.dataset.litrosPorCilindro);
  return Math.max((openCylinders * capacity) - used, 0);
}

function chooseAvailableOrigin(product, origin) {
  if (!product || origin.value !== "suelto") return;
  const loose = toNumber(product.dataset.stockSuelto);
  if (loose > 0) return;
  if (cylinderAvailable(product) > 0) {
    origin.value = "cilindro_abierto";
    return;
  }
  if (toNumber(product.dataset.baldesAbiertos) > 0) {
    origin.value = "balde_abierto";
  }
}

function updateLine(row) {
  const product = selectedProduct(row);
  const origin = row.querySelector("[data-line-origin]");
  const quantity = row.querySelector("[data-line-quantity]");
  const stock = row.querySelector("[data-line-stock]");
  const quantityHint = row.querySelector("[data-quantity-hint]");
  if (!product) {
    stock.textContent = "-";
    if (quantityHint) quantityHint.hidden = true;
    updateGallonShortcuts(row, null);
    return;
  }

  chooseAvailableOrigin(product, origin);
  const originValue = origin.value;
  const abbreviation = displayAbbreviation(product);
  const allowsDecimal = product.dataset.decimal === "1";
  quantity.step = allowsDecimal ? "0.001" : "1";
  quantity.min = allowsDecimal ? "0.001" : "1";
  if (quantityHint) {
    quantityHint.hidden = !isGallonProduct(product);
    quantityHint.textContent = isGallonProduct(product)
      ? "Escribe litros o usa una fraccion de galon."
      : "";
  }
  updateGallonShortcuts(row, product);
  if (originValue === "balde_abierto") {
    const openBuckets = toNumber(product.dataset.baldesAbiertos);
    const used = toNumber(product.dataset.stockBaldeAbierto);
    quantity.removeAttribute("max");
    stock.textContent = openBuckets > 0
      ? `${formatQuantity(openBuckets)} balde(s) / usado ${formatStockForProduct(used, product)}`
      : "Sin balde abierto";
    return;
  }

  if (originValue === "cilindro_abierto") {
    const openCylinders = toNumber(product.dataset.cilindrosAbiertos);
    const used = toNumber(product.dataset.stockCilindroAbierto);
    const capacity = toNumber(product.dataset.litrosPorCilindro);
    const available = cylinderAvailable(product);
    quantity.max = String(available);
    stock.textContent = openCylinders > 0 && capacity > 0
      ? `${formatQuantity(openCylinders)} cilindro(s) / queda ${formatStockForProduct(available, product)}`
      : openCylinders > 0
        ? "Falta capacidad del cilindro"
      : "Sin cilindro abierto";
    return;
  }

  const available = toNumber(product.dataset.stockSuelto);
  quantity.max = String(available);
  stock.textContent = formatStockForProduct(available, product);
}

function addLine() {
  const fragment = lineTemplate.content.cloneNode(true);
  const row = fragment.querySelector("[data-output-line]");
  const areaSelect = row.querySelector("[data-line-area]");
  const typeSelect = row.querySelector("[data-line-type]");
  const categorySelect = row.querySelector("[data-line-category]");
  const productSelect = row.querySelector("[data-line-product]");
  areaSelect.addEventListener("change", () => {
    syncProductPicker(areaSelect, typeSelect, categorySelect, productSelect);
    updateLine(row);
  });
  typeSelect.addEventListener("change", () => {
    syncProductPicker(areaSelect, typeSelect, categorySelect, productSelect);
    updateLine(row);
  });
  categorySelect.addEventListener("change", () => {
    syncProductPicker(areaSelect, typeSelect, categorySelect, productSelect);
    updateLine(row);
  });
  productSelect.addEventListener("change", () => updateLine(row));
  row.querySelector("[data-line-origin]").addEventListener("change", () => updateLine(row));
  row.querySelectorAll("[data-gallon-fraction]").forEach((button) => {
    button.addEventListener("click", () => {
      const product = selectedProduct(row);
      const liters = gallonLiters(product);
      if (!liters) return;
      row.querySelector("[data-line-quantity]").value = formatInputQuantity(
        liters * toNumber(button.dataset.gallonFraction)
      );
      updateLine(row);
    });
  });
  row.querySelector("[data-remove-line]").addEventListener("click", () => {
    if (linesContainer.children.length > 1) row.remove();
  });
  linesContainer.appendChild(row);
  if (window.enhanceScrollSelects) {
    window.enhanceScrollSelects(row);
  }
  syncProductPicker(areaSelect, typeSelect, categorySelect, productSelect);
  updateLine(row);
}

vehiclePlate.addEventListener("change", syncVehicleModel);
vehiclePlate.addEventListener("blur", syncVehicleModel);
addLineButton.addEventListener("click", addLine);

cancelOutputForms.forEach((form) => {
  form.addEventListener("submit", (event) => {
    const destination = form.dataset.destination || "esta salida";
    const reason = window.prompt(`Motivo para anular la salida de ${destination}:`);
    if (!reason || !reason.trim()) {
      event.preventDefault();
      return;
    }
    form.querySelector("input[name='motivo']").value = reason.trim();
  });
});

document.querySelectorAll("[data-correct-output-detail]").forEach((button) => {
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

document.querySelectorAll("[data-close-output-correction]").forEach((button) => {
  button.addEventListener("click", () => {
    if (correctionDialog?.open) correctionDialog.close();
  });
});

addLine();
