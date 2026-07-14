(function () {
  const SELECTOR = "select:not([data-native-select])";
  const enhanced = new WeakSet();
  const controllers = new WeakMap();
  const instances = new Set();

  function optionIsVisible(option) {
    return !option.hidden && !option.disabled;
  }

  function getSelectedLabel(select) {
    const selected = select.options[select.selectedIndex];
    if (selected && selected.value && !selected.hidden) {
      return selected.textContent.trim();
    }

    const placeholder = Array.from(select.options).find((option) => !option.value);
    return placeholder?.textContent.trim() || "Selecciona";
  }

  function closeAll(except = null) {
    instances.forEach((instance) => {
      if (instance !== except) instance.close();
    });
  }

  function enhanceSelect(select) {
    if (!select || enhanced.has(select) || select.multiple || select.size > 1) return;

    enhanced.add(select);

    const wrapper = document.createElement("div");
    wrapper.className = "scroll-select";
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);
    select.classList.add("scroll-select-native");

    const button = document.createElement("button");
    button.type = "button";
    button.className = "scroll-select-button";
    button.setAttribute("aria-haspopup", "listbox");
    button.setAttribute("aria-expanded", "false");
    button.innerHTML = '<span data-scroll-select-label></span><span class="material-symbols-outlined" aria-hidden="true">expand_more</span>';

    const menu = document.createElement("div");
    menu.className = "scroll-select-menu";
    menu.setAttribute("role", "listbox");
    menu.hidden = true;

    wrapper.append(button, menu);

    const label = button.querySelector("[data-scroll-select-label]");
    let validationShown = false;

    function sync() {
      label.textContent = getSelectedLabel(select);
      button.disabled = select.disabled;
      button.classList.toggle("is-invalid", validationShown && !select.validity.valid && select.required);
    }

    function buildMenu() {
      menu.innerHTML = "";

      const options = Array.from(select.options).filter((option) => !option.hidden);
      if (!options.length) {
        const empty = document.createElement("div");
        empty.className = "scroll-select-empty";
        empty.textContent = "Sin opciones";
        menu.appendChild(empty);
        return;
      }

      options.forEach((option) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "scroll-select-option";
        item.textContent = option.textContent.trim();
        item.dataset.value = option.value;
        item.disabled = !optionIsVisible(option);
        item.setAttribute("role", "option");
        item.setAttribute("aria-selected", option.selected ? "true" : "false");
        item.classList.toggle("active", option.selected);

        item.addEventListener("click", () => {
          if (item.disabled) return;
          select.value = option.value;
          select.dispatchEvent(new Event("input", { bubbles: true }));
          select.dispatchEvent(new Event("change", { bubbles: true }));
          if (select.validity.valid) validationShown = false;
          close();
          sync();
        });

        menu.appendChild(item);
      });
    }

    function open() {
      if (select.disabled) return;
      closeAll(instance);
      buildMenu();
      wrapper.classList.add("open");
      button.setAttribute("aria-expanded", "true");
      menu.hidden = false;

      const active = menu.querySelector(".scroll-select-option.active");
      if (active) active.scrollIntoView({ block: "nearest" });
    }

    function close() {
      wrapper.classList.remove("open");
      button.setAttribute("aria-expanded", "false");
      menu.hidden = true;
    }

    const instance = { close, wrapper };
    instances.add(instance);
    controllers.set(select, { sync });

    button.addEventListener("click", () => {
      if (menu.hidden) open();
      else close();
    });

    select.addEventListener("change", () => {
      if (select.validity.valid) validationShown = false;
      sync();
    });
    select.addEventListener("invalid", () => {
      validationShown = true;
      sync();
      button.focus();
    });

    const observer = new MutationObserver(sync);
    observer.observe(select, {
      attributes: true,
      attributeFilter: ["disabled", "hidden", "label", "selected", "value"],
      childList: true,
      subtree: true,
    });

    sync();
  }

  window.enhanceScrollSelects = function (root = document) {
    root.querySelectorAll(SELECTOR).forEach(enhanceSelect);
  };

  window.refreshScrollSelects = function (root = document) {
    root.querySelectorAll(SELECTOR).forEach((select) => {
      controllers.get(select)?.sync();
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    window.enhanceScrollSelects(document);
  });

  document.addEventListener("click", (event) => {
    instances.forEach((instance) => {
      if (!instance.wrapper.contains(event.target)) instance.close();
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });
})();
