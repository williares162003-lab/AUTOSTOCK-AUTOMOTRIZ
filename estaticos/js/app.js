const botonNotificaciones = document.querySelector("#btn-notificaciones");
const panelNotificaciones = document.querySelector("#notif-panel");
const cerrarNotificaciones = document.querySelector("#btn-cerrar-notificaciones");
const fondoNotificaciones = document.querySelector("#notif-backdrop");

function alternarNotificaciones() {
    panelNotificaciones?.classList.toggle("hidden");
    fondoNotificaciones?.classList.toggle("hidden");
}

botonNotificaciones?.addEventListener("click", alternarNotificaciones);
cerrarNotificaciones?.addEventListener("click", alternarNotificaciones);
fondoNotificaciones?.addEventListener("click", alternarNotificaciones);
