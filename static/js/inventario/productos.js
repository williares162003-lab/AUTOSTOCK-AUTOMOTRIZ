const productDialog = document.querySelector("[data-product-dialog]");
const productForm = document.querySelector("[data-product-form]");
const areaSelect = productForm.querySelector("[data-form-area]");
const typeSelect = productForm.elements.tipo_id;
const categorySelect = productForm.elements.categoria_id;
const unitSelect = productForm.elements.unidad_base_id;
const initialStockField = productForm.querySelector("[data-initial-stock]");
const initialStockLabel = productForm.querySelector("[data-initial-stock-label]");
const initialStockInput = productForm.elements.stock_actual;
const initialGallonLitersField = productForm.querySelector("[data-initial-gallon-liters]");
const initialGallonLitersInput = productForm.elements.litros_por_galon;
const presentationList = document.querySelector("[data-presentation-list]");

function filterFormTypes(selectedType = "") {
  const areaId = areaSelect.value;
  let firstVisible = null;
  Array.from(typeSelect.options).forEach((option) => {
    const visible = option.dataset.area === areaId;
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible && !firstVisible) firstVisible = option;
  });
  const selected = Array.from(typeSelect.options).find(
    (option) => option.value === String(selectedType) && !option.hidden
  );
  typeSelect.value = (selected || firstVisible)?.value || "";
}

function filterFormCategories(selectedCategory = "") {
  const typeId = typeSelect.value;
  let firstVisible = null;
  Array.from(categorySelect.options).forEach((option) => {
    const visible = option.dataset.type === typeId && option.dataset.area === areaSelect.value;
    option.hidden = !visible;
    option.disabled = !visible;
    if (visible && !firstVisible) firstVisible = option;
  });
  const selected = Array.from(categorySelect.options).find(
    (option) => option.value === String(selectedCategory) && !option.hidden
  );
  categorySelect.value = (selected || firstVisible)?.value || "";
}

function addPresentation(presentation = {}) {
  const row = document.createElement("div");
  row.className = "presentation-row";
  row.innerHTML = `
    <label><span>Presentacion</span><input name="presentacion_nombre" maxlength="80" placeholder="Balde" value=""></label>
    <label><span>Equivale a</span><input name="presentacion_factor" type="number" min="0.001" step="0.001" placeholder="5" value=""></label>
    <button class="icon-action danger" type="button" title="Quitar presentacion"><span class="material-symbols-outlined">delete</span></button>
  `;
  row.querySelector('[name="presentacion_nombre"]').value = presentation.nombre || "";
  row.querySelector('[name="presentacion_factor"]').value = presentation.factor || "";
  row.querySelector("button").addEventListener("click", () => row.remove());
  presentationList.appendChild(row);
}

function selectedUnitIsGallon() {
  const option = unitSelect.selectedOptions[0];
  const text = `${option?.dataset.abreviatura || ""} ${option?.textContent || ""}`
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  return text.includes("gal");
}

function syncInitialStockFields() {
  const showGallonLiters = !initialStockField.hidden && selectedUnitIsGallon();
  initialGallonLitersField.hidden = !showGallonLiters;
  initialGallonLitersInput.disabled = !showGallonLiters;
  initialStockInput.step = showGallonLiters ? "1" : "0.001";
  initialStockInput.min = "0";
  initialStockLabel.textContent = showGallonLiters
    ? "Cantidad inicial de galones/envases"
    : "Stock inicial";
}

function openCreateProduct() {
  productForm.reset();
  productForm.action = window.productCreateUrl;
  document.querySelector("[data-dialog-title]").textContent = "Nuevo producto";
  initialStockField.hidden = false;
  initialStockInput.disabled = false;
  presentationList.innerHTML = "";
  filterFormTypes();
  filterFormCategories();
  syncInitialStockFields();
  productDialog.showModal();
}

document.querySelector("[data-open-product]").addEventListener("click", openCreateProduct);
areaSelect.addEventListener("change", () => {
  filterFormTypes();
  filterFormCategories();
});
typeSelect.addEventListener("change", () => filterFormCategories());
unitSelect.addEventListener("change", syncInitialStockFields);
document.querySelector("[data-add-presentation]").addEventListener("click", () => addPresentation());

document.querySelectorAll("[data-edit-product]").forEach((button) => {
  button.addEventListener("click", () => {
    productForm.reset();
    productForm.action = button.dataset.action;
    document.querySelector("[data-dialog-title]").textContent = "Editar producto";
    const fields = {
      nombre: "nombre",
      codigo: "codigo",
      marca: "marca",
      descripcion: "descripcion",
      unidad_base_id: "unidadBaseId",
      stock_minimo: "stockMinimo",
      observaciones: "observaciones",
    };
    Object.entries(fields).forEach(([field, dataKey]) => {
      productForm.elements[field].value = button.dataset[dataKey] || "";
    });
    areaSelect.value = button.dataset.areaId;
    filterFormTypes(button.dataset.tipoId);
    filterFormCategories(button.dataset.categoriaId);
    initialStockField.hidden = true;
    initialStockInput.disabled = true;
    presentationList.innerHTML = "";
    JSON.parse(button.dataset.presentaciones || "[]").forEach(addPresentation);
    syncInitialStockFields();
    productDialog.showModal();
  });
});

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

const detailDialog = document.querySelector("[data-detail-dialog]");
const detailPresentations = document.querySelector("[data-detail-presentations]");
document.querySelectorAll("[data-view-product]").forEach((button) => {
  button.addEventListener("click", () => {
    detailDialog.querySelector("[data-detail-name]").textContent = button.dataset.nombre;
    detailDialog.querySelector("[data-detail-meta]").textContent = `${button.dataset.tipo} / ${button.dataset.categoria}`;
    const stockUnit = button.dataset.stockUnidad || button.dataset.abreviatura;
    detailDialog.querySelector("[data-detail-stock]").textContent = button.dataset.stockResumen || `${button.dataset.stock} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-stock-loose]").textContent = button.dataset.stockSueltoResumen || `${button.dataset.stockSuelto} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-open-buckets]").textContent = `${button.dataset.baldesAbiertos} balde(s)`;
    detailDialog.querySelector("[data-detail-stock-open-bucket]").textContent = `${button.dataset.stockBaldeAbierto} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-stock-closed-buckets]").textContent = `${button.dataset.stockBaldesCerrados} balde(s)`;
    detailDialog.querySelector("[data-detail-open-cylinders]").textContent = `${button.dataset.cilindrosAbiertos} cilindro(s)`;
    detailDialog.querySelector("[data-detail-stock-open-cylinder]").textContent = `${button.dataset.stockCilindroAbierto} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-stock-closed-cylinders]").textContent = `${button.dataset.stockCilindrosCerrados} cilindro(s)`;
    detailDialog.querySelector("[data-detail-cylinder-liters]").textContent = `${button.dataset.litrosPorCilindro} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-closed-boxes]").textContent = `${button.dataset.stockCajasCerradas || 0} caja(s)`;
    detailDialog.querySelector("[data-detail-box-units]").textContent = `${button.dataset.unidadesPorCaja || 0} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-total-stock]").textContent = `${button.dataset.stockTotal || button.dataset.stock} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-minimum]").textContent = `${button.dataset.minimo} ${stockUnit}`;
    detailDialog.querySelector("[data-detail-status]").textContent = button.dataset.estado;
    detailDialog.querySelector("[data-detail-area]").textContent = button.dataset.area;
    detailDialog.querySelector("[data-detail-type]").textContent = button.dataset.tipo;
    detailDialog.querySelector("[data-detail-category]").textContent = button.dataset.categoria;
    detailDialog.querySelector("[data-detail-unit]").textContent = `${button.dataset.unidad} (${button.dataset.abreviatura})`;
    detailDialog.querySelector("[data-detail-code]").textContent = button.dataset.codigo || "Sin codigo";
    detailDialog.querySelector("[data-detail-brand]").textContent = button.dataset.marca;
    detailDialog.querySelector("[data-detail-description]").textContent = button.dataset.descripcion;
    detailDialog.querySelector("[data-detail-notes]").textContent = button.dataset.observaciones;

    detailPresentations.innerHTML = "";
    const presentations = JSON.parse(button.dataset.presentaciones || "[]");
    if (!presentations.length) {
      const empty = document.createElement("small");
      empty.textContent = "Unidad base";
      detailPresentations.appendChild(empty);
    }
    presentations.forEach((presentation) => {
      const tag = document.createElement("span");
      tag.textContent = `${presentation.nombre} = ${presentation.factor} ${button.dataset.abreviatura}`;
      detailPresentations.appendChild(tag);
    });
    detailDialog.showModal();
  });
});

const stockDialog = document.querySelector("[data-stock-dialog]");
const stockForm = document.querySelector("[data-stock-form]");
document.querySelectorAll("[data-adjust-stock]").forEach((button) => {
  button.addEventListener("click", () => {
    stockForm.reset();
    stockForm.action = button.dataset.action;
    stockDialog.querySelector("[data-stock-product]").textContent = button.dataset.nombre;
    stockDialog.querySelector("[data-current-stock]").textContent = `${button.dataset.stock} ${button.dataset.unidad}`;
    const looseInput = stockDialog.querySelector("[data-new-stock-loose]");
    const openBucketInput = stockDialog.querySelector("[data-new-stock-open-bucket]");
    const openBucketsInput = stockDialog.querySelector("[data-new-open-buckets]");
    const closedBucketsInput = stockDialog.querySelector("[data-new-stock-closed-buckets]");
    const openCylinderInput = stockDialog.querySelector("[data-new-stock-open-cylinder]");
    const openCylindersInput = stockDialog.querySelector("[data-new-open-cylinders]");
    const closedCylindersInput = stockDialog.querySelector("[data-new-stock-closed-cylinders]");
    const cylinderLitersInput = stockDialog.querySelector("[data-new-cylinder-liters]");
    const gallonLitersInput = stockDialog.querySelector("[data-new-gallon-liters]");
    const closedBoxesInput = stockDialog.querySelector("[data-new-stock-closed-boxes]");
    const boxUnitsInput = stockDialog.querySelector("[data-new-box-units]");
    const step = button.dataset.decimal === "1" ? "0.001" : "1";
    looseInput.value = button.dataset.stockSuelto;
    openBucketInput.value = button.dataset.stockBaldeAbierto;
    openBucketsInput.value = button.dataset.baldesAbiertos;
    closedBucketsInput.value = button.dataset.stockBaldesCerrados;
    openCylinderInput.value = button.dataset.stockCilindroAbierto;
    openCylindersInput.value = button.dataset.cilindrosAbiertos;
    closedCylindersInput.value = button.dataset.stockCilindrosCerrados;
    cylinderLitersInput.value = button.dataset.litrosPorCilindro;
    gallonLitersInput.value = button.dataset.litrosPorGalon || "0";
    closedBoxesInput.value = button.dataset.stockCajasCerradas || "0";
    boxUnitsInput.value = button.dataset.unidadesPorCaja || "0";
    looseInput.step = step;
    openBucketInput.step = step;
    openCylinderInput.step = step;
    boxUnitsInput.step = step;
    stockDialog.showModal();
  });
});

document.querySelectorAll("[data-delete-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(`Eliminar ${form.dataset.name}?`)) event.preventDefault();
  });
});

const productRows = Array.from(document.querySelectorAll("[data-product-row]"));
const productSearch = document.querySelector("[data-product-search]");
const areaFilter = document.querySelector("[data-area-filter]");
const typeFilter = document.querySelector("[data-type-filter]");
const categoryFilter = document.querySelector("[data-category-filter]");
const statusFilter = document.querySelector("[data-status-filter]");
const productCount = document.querySelector("[data-product-count]");
const filterEmpty = document.querySelector("[data-filter-empty]");

function filterProducts() {
  const search = productSearch.value.trim().toLowerCase();
  let visible = 0;
  productRows.forEach((row) => {
    const matches = row.dataset.search.includes(search)
      && (!areaFilter.value || row.dataset.area === areaFilter.value)
      && (!typeFilter.value || row.dataset.type === typeFilter.value)
      && (!categoryFilter.value || row.dataset.category === categoryFilter.value)
      && (!statusFilter.value || row.dataset.status === statusFilter.value);
    row.hidden = !matches;
    if (matches) visible += 1;
  });
  productCount.textContent = String(visible);
  filterEmpty.hidden = visible !== 0;
}

function syncFilterOptions() {
  Array.from(typeFilter.options).forEach((option) => {
    if (!option.value) return;
    const visible = !areaFilter.value || option.dataset.area === areaFilter.value;
    option.hidden = !visible;
    option.disabled = !visible;
  });
  if (typeFilter.selectedOptions[0]?.disabled) typeFilter.value = "";
  Array.from(categoryFilter.options).forEach((option) => {
    if (!option.value) return;
    const visible = (!areaFilter.value || option.dataset.area === areaFilter.value)
      && (!typeFilter.value || option.dataset.type === typeFilter.value);
    option.hidden = !visible;
    option.disabled = !visible;
  });
  if (categoryFilter.selectedOptions[0]?.disabled) categoryFilter.value = "";
  window.refreshScrollSelects?.(document.querySelector(".inventory-filters"));
}

[productSearch, areaFilter, typeFilter, categoryFilter, statusFilter].forEach((control) => {
  control.addEventListener("input", () => {
    syncFilterOptions();
    filterProducts();
  });
});

syncFilterOptions();
