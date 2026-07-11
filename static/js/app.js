document.querySelectorAll(".nav-parent").forEach((button) => {
  button.addEventListener("click", () => {
    button.closest(".nav-group")?.classList.toggle("open");
  });
});
