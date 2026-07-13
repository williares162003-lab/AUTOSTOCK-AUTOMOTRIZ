const productDialog = document.querySelector("[data-product-dialog]");
const productForm = document.querySelector("[data-product-form]");
const typeSelect = productForm.elements.tipo_id;
const categorySelect = productForm.elements.categoria_id;
const presentationList = document.querySelector("[data-presentation-list]");

function filterFormCategories(selectedCategory = "") {
  const typeId = typeSelect.value;
  let firstVisible = null;
  Array.from(categorySelect.options).forEach((option) => {
    const visible = option.dataset.type === typeId;
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

function openCreateProduct() {
  productForm.reset();
  productForm.action = window.productCreateUrl;
  document.querySelector("[data-dialog-title]").textContent = "Nuevo producto";
  document.querySelector("[data-initial-stock]").hidden = false;
  productForm.elements.stock_actual.disabled = false;
  presentationList.innerHTML = "";
  filterFormCategories();
  productDialog.showModal();
}

document.querySelector("[data-open-product]").addEventListener("click", openCreateProduct);
typeSelect.addEventListener("change", () => filterFormCategories());
document.querySelector("[data-add-presentation]").addEventListener("click", () => addPresentation());

document.querySelectorAll("[data-edit-product]").forEach((button) => {
  button.addEventListener("click", () => {
    productForm.reset();
    productForm.action = button.dataset.action;
    document.querySelector("[data-dialog-title]").textContent = "Editar producto";
    const fields = {
      nombre: "nombre",
      marca: "marca",
      descripcion: "descripcion",
      unidad_base_id: "unidadBaseId",
      stock_minimo: "stockMinimo",
      observaciones: "observaciones",
    };
    Object.entries(fields).forEach(([field, dataKey]) => {
      productForm.elements[field].value = button.dataset[dataKey] || "";
    });
    typeSelect.value = button.dataset.tipoId;
    filterFormCategories(button.dataset.categoriaId);
    document.querySelector("[data-initial-stock]").hidden = true;
    productForm.elements.stock_actual.disabled = true;
    presentationList.innerHTML = "";
    JSON.parse(button.dataset.presentaciones || "[]").forEach(addPresentation);
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
    detailDialog.querySelector("[data-detail-stock]").textContent = `${button.dataset.stock} ${button.dataset.abreviatura}`;
    detailDialog.querySelector("[data-detail-stock-loose]").textContent = `${button.dataset.stockSuelto} ${button.dataset.abreviatura}`;
    detailDialog.querySelector("[data-detail-open-buckets]").textContent = `${button.dataset.baldesAbiertos} balde(s)`;
    detailDialog.querySelector("[data-detail-stock-open-bucket]").textContent = `${button.dataset.stockBaldeAbierto} ${button.dataset.abreviatura}`;
    detailDialog.querySelector("[data-detail-stock-closed-buckets]").textContent = `${button.dataset.stockBaldesCerrados} balde(s)`;
    detailDialog.querySelector("[data-detail-minimum]").textContent = `${button.dataset.minimo} ${button.dataset.abreviatura}`;
    detailDialog.querySelector("[data-detail-status]").textContent = button.dataset.estado;
    detailDialog.querySelector("[data-detail-type]").textContent = button.dataset.tipo;
    detailDialog.querySelector("[data-detail-category]").textContent = button.dataset.categoria;
    detailDialog.querySelector("[data-detail-unit]").textContent = `${button.dataset.unidad} (${button.dataset.abreviatura})`;
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
    const step = button.dataset.decimal === "1" ? "0.001" : "1";
    looseInput.value = button.dataset.stockSuelto;
    openBucketInput.value = button.dataset.stockBaldeAbierto;
    openBucketsInput.value = button.dataset.baldesAbiertos;
    closedBucketsInput.value = button.dataset.stockBaldesCerrados;
    looseInput.step = step;
    openBucketInput.step = step;
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
      && (!typeFilter.value || row.dataset.type === typeFilter.value)
      && (!categoryFilter.value || row.dataset.category === categoryFilter.value)
      && (!statusFilter.value || row.dataset.status === statusFilter.value);
    row.hidden = !matches;
    if (matches) visible += 1;
  });
  productCount.textContent = String(visible);
  filterEmpty.hidden = visible !== 0;
}

[productSearch, typeFilter, categoryFilter, statusFilter].forEach((control) => control.addEventListener("input", filterProducts));
