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
  const quantity = row.querySelector("[data-line-quantity]");
  const stock = row.querySelector("[data-line-stock]");
  if (!product) {
    stock.textContent = "-";
    return;
  }

  const available = toNumber(product.dataset.stock);
  const abbreviation = product.dataset.abreviatura;
  quantity.step = product.dataset.decimal === "1" ? "0.001" : "1";
  quantity.max = String(available);
  stock.textContent = `${formatQuantity(available)} ${abbreviation}`;
}

function addLine() {
  const fragment = lineTemplate.content.cloneNode(true);
  const row = fragment.querySelector("[data-output-line]");
  row.querySelector("[data-line-product]").addEventListener("change", () => updateLine(row));
  row.querySelector("[data-remove-line]").addEventListener("click", () => {
    if (linesContainer.children.length > 1) row.remove();
  });
  linesContainer.appendChild(row);
  updateLine(row);
}

vehiclePlate.addEventListener("change", syncVehicleModel);
vehiclePlate.addEventListener("blur", syncVehicleModel);
addLineButton.addEventListener("click", addLine);

addLine();
