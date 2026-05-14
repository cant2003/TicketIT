let currentStatus = "",
  sortState = { col: null, dir: 1 },
  tableData = { columns: [], rows: [] },
  selectedTicket = null;
function showToast(msg, type = "success") {
  const box = document.getElementById("toasts");
  if (!box) return;
  const id = "t" + Date.now();
  const bg =
    type === "danger"
      ? "text-bg-danger"
      : type === "warning"
        ? "text-bg-warning"
        : "text-bg-success";
  box.insertAdjacentHTML(
    "beforeend",
    `<div id="${id}" class="toast ${bg}" role="alert"><div class="d-flex"><div class="toast-body">${msg}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`,
  );
  const el = document.getElementById(id);
  new bootstrap.Toast(el, { delay: 4200 }).show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
}
function confirmBox(title, body, okText = "Confirmar") {
  return new Promise((resolve) => {
    document.getElementById("confirmTitle").textContent = title;
    document.getElementById("confirmBody").textContent = body;
    const ok = document.getElementById("confirmOk");
    ok.textContent = okText;
    const modal = new bootstrap.Modal("#confirmModal");
    const handler = () => {
      ok.removeEventListener("click", handler);
      modal.hide();
      resolve(true);
    };
    ok.addEventListener("click", handler);
    document
      .getElementById("confirmModal")
      .addEventListener("hidden.bs.modal", () => resolve(false), {
        once: true,
      });
    modal.show();
  });
}
async function confirmLogout() {
  if (
    await confirmBox(
      "Cerrar sesión",
      "¿Seguro que deseas salir del panel?",
      "Salir",
    )
  )
    location.href = "/logout";
}
async function stats() {
  return await (await fetch("/api/stats")).json();
}
async function pollHome() {
  let last = +(sessionStorage.getItem("lastTickets") || 0),
    s = await stats(),
    bt = document.getElementById("badge-tickets");
  if (s.tickets_new > 0 && bt) {
    bt.textContent = s.tickets_new;
    bt.classList.remove("hidden");
  }
  if (+s.tickets_new > last)
    showToast(`Hay ${s.tickets_new} tickets nuevos`, "success");
  sessionStorage.setItem("lastTickets", s.tickets_new);
}
function rowClass(r) {
  let v = Object.values(r).join(" ").toLowerCase();
  if (v.includes("abiert") || v.includes("open") || v.includes("nuevo"))
    return "table-success";
  if (v.includes("proceso") || v.includes("pend")) return "table-warning";
  if (
    v.includes("cerr") ||
    v.includes("closed") ||
    v.includes("resuelto") ||
    v.includes("cancel")
  )
    return "table-danger";
  return "";
}
async function loadTable() {
  let kind = window.TABLE_KIND || "tickets";
  const q = new URLSearchParams({
    search: document.getElementById("search")?.value || "",
    status: currentStatus,
  });
  const data = await (await fetch(`/api/table/${kind}?${q}`)).json();
  tableData = data;
  renderTable(kind);
  if (kind === "tickets") {
    let s = await stats();
    ["total", "abiertos", "proceso", "cerrados"].forEach((id) => {
      let e = document.getElementById(id);
      if (e) e.textContent = s[id] || 0;
    });
  }
}
function renderTable(kind) {
  const t = document.getElementById("data-table");
  if (!t) return;
  let cols = tableData.columns || [],
    rows = [...(tableData.rows || [])];
  if (sortState.col) {
    rows.sort(
      (a, b) =>
        String(a[sortState.col] ?? "").localeCompare(
          String(b[sortState.col] ?? ""),
          undefined,
          { numeric: true, sensitivity: "base" },
        ) * sortState.dir,
    );
  }
  if (!rows.length) {
    t.innerHTML =
      '<tbody><tr><td class="text-center text-muted py-5">Sin registros para mostrar</td></tr></tbody>';
    return;
  }
  let head = "<thead><tr>";
  if (kind === "users") head += "<th>Seleccionar</th>";
  head += cols
    .map(
      (c) =>
        `<th role="button" onclick="sortBy('${String(c).replaceAll("'", "\\'")}')">${c} <i class="bi bi-arrow-down-up small opacity-50"></i></th>`,
    )
    .join("");
  if (kind === "tickets") head += "<th>Opciones</th>";
  head += "</tr></thead>";
  let body =
    "<tbody>" +
    rows
      .map((row) => {
        let tr = `<tr class="${kind === "tickets" ? rowClass(row) : ""}">`;
        if (kind === "users")
          tr += `<td><input class="form-check-input user-radio" type="radio" name="userPick" value="${getTelegramId(row)}"></td>`;
        tr += cols.map((c) => {
            let value = row[c] ?? "";

            if (
                c.toLowerCase().includes("fecha") ||
                c.toLowerCase().includes("created") ||
                c.toLowerCase().includes("updated")
            ) {
                value = formatDate(value);
            }

            return `<td>${escapeHtml(value)}</td>`;
        }).join("");
        if (kind === "tickets")
          tr += `<td><button class="btn btn-sm btn-primary rounded-pill" onclick='openTicket(${JSON.stringify(row).replaceAll("'", "&#39;")})'><i class="bi bi-pencil-square me-1"></i>Ver / Editar</button></td>`;
        return tr + "</tr>";
      })
      .join("") +
    "</tbody>";
  t.innerHTML = head + body;
}

function formatDate(fecha) {
    if (!fecha) return "-";

    const d = new Date(fecha);

    if (isNaN(d.getTime())) return fecha;

    const dia = String(d.getDate()).padStart(2, "0");
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const anio = d.getFullYear();

    const horas = String(d.getHours()).padStart(2, "0");
    const minutos = String(d.getMinutes()).padStart(2, "0");
    const segundos = String(d.getSeconds()).padStart(2, "0");

    return `${dia}-${mes}-${anio} ${horas}:${minutos}:${segundos}`;
}


function escapeHtml(x) {
  return String(x).replace(
    /[&<>"]/g,
    (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[m],
  );
}
function sortBy(col) {
  sortState.dir = sortState.col === col ? sortState.dir * -1 : 1;
  sortState.col = col;
  renderTable(window.TABLE_KIND || "tickets");
}
function setStatusFilter(v, btn) {
  currentStatus = v;
  document
    .querySelectorAll(".stat-card")
    .forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  loadTable();
}
function clearFilters() {
  currentStatus = "";
  let s = document.getElementById("search");
  if (s) s.value = "";
  document
    .querySelectorAll(".stat-card")
    .forEach((b) => b.classList.remove("active"));
  document.querySelector('.stat-card[data-filter=""]')?.classList.add("active");
  loadTable();
}
function openTicket(row) {
  selectedTicket = row;
  const form = document.getElementById("ticketForm");
  form.innerHTML = "";
  tableData.columns.forEach((c) => {
    let value = row[c] ?? "",
      lower = c.toLowerCase();
    let editable = !(
      lower === "id" ||
      lower.includes("fecha") ||
      lower.includes("crea") ||
      lower.includes("actualiz")
    );
    let field;
    if (lower.includes("descripcion") || lower.includes("observ"))
      field = `<textarea class="form-control" rows="3" name="${c}" ${editable ? "" : "readonly"}>${escapeHtml(value)}</textarea>`;
    else
      field = `<input class="form-control" name="${c}" value="${escapeHtml(value)}" ${editable ? "" : "readonly"}>`;
    form.insertAdjacentHTML(
      "beforeend",
      `<div class="col-md-6"><label class="form-label fw-semibold">${c}</label>${field}</div>`,
    );
  });
  new bootstrap.Modal("#ticketModal").show();
}
async function saveTicket() {
  if (!selectedTicket) return;
  if (
    !(await confirmBox(
      "Guardar cambios",
      "¿Deseas guardar los cambios de este ticket?",
      "Guardar",
    ))
  )
    return;
  const form = document.getElementById("ticketForm");
  let body = {};
  [...form.elements].forEach((e) => {
    if (e.name && !e.readOnly) body[e.name] = e.value;
  });
  const r = await fetch(`/api/tickets/${selectedTicket._rowid}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json().catch(() => ({}));
  showToast(
    r.ok ? "Ticket actualizado" : j.msg || "No se pudo actualizar",
    r.ok ? "success" : "danger",
  );
  if (r.ok) {
    bootstrap.Modal.getInstance(document.getElementById("ticketModal")).hide();
    loadTable();
  }
}
async function sendTicketsEmail() {
  if (
    !(await confirmBox(
      "Enviar reporte",
      "Se enviará el Excel al correo configurado en .env. ¿Continuar?",
      "Enviar",
    ))
  )
    return;
  const r = await fetch("/api/email/tickets", { method: "POST" });
  const j = await r.json().catch(() => ({}));
  showToast(
    r.ok ? "Reporte enviado correctamente" : j.msg || "No se pudo enviar",
    r.ok ? "success" : "danger",
  );
}
function getTelegramId(row) {
  let keys = Object.keys(row),
    k =
      keys.find((x) =>
        [
          "telegram_id",
          "chat_id",
          "id_telegram",
          "telegram",
          "user_id",
        ].includes(x.toLowerCase()),
      ) ||
      keys.find((x) => x.toLowerCase().includes("telegram")) ||
      keys[1] ||
      keys[0];
  return row[k] ?? "";
}
async function addUserFromForm() {
  let id = document.getElementById("newTelegramId").value.trim(),
    nombre = document.getElementById("newTiName").value.trim();
  if (!id) {
    showToast("Debes ingresar un ID de Telegram", "warning");
    return;
  }
  if (
    !(await confirmBox(
      "Agregar TI",
      `¿Guardar el ID ${id} como TI autorizado?`,
      "Guardar",
    ))
  )
    return;
  const r = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id: id, nombre }),
  });
  const j = await r.json().catch(() => ({}));
  showToast(
    r.ok ? "TI agregado correctamente" : j.msg || "No se pudo agregar",
    r.ok ? "success" : "danger",
  );
  if (r.ok) {
    bootstrap.Modal.getInstance(document.getElementById("userModal")).hide();
    document.getElementById("newTelegramId").value = "";
    document.getElementById("newTiName").value = "";
    loadTable();
  }
}
async function deleteSelectedUser() {
  let picked = document.querySelector(".user-radio:checked");
  if (!picked) {
    showToast("Selecciona un TI de la tabla para eliminar", "warning");
    return;
  }
  if (
    !(await confirmBox(
      "Eliminar TI",
      `¿Seguro que deseas eliminar el ID ${picked.value}?`,
      "Eliminar",
    ))
  )
    return;
  const r = await fetch("/api/users", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id: picked.value }),
  });
  const j = await r.json().catch(() => ({}));
  showToast(
    r.ok ? "TI eliminado correctamente" : j.msg || "No se pudo eliminar",
    r.ok ? "success" : "danger",
  );
  loadTable();
}
async function launcherStatus() {
  const s = await (await fetch("/api/launcher/status")).json();
  ["webhook", "worker", "ngrok"].forEach((k) => {
    let e = document.getElementById("s-" + k);
    if (e) e.textContent = s[k] ? "ENCENDIDO" : "APAGADO";
  });
  document.querySelectorAll(".form-switch-btn").forEach((b) => {
    let k = b.dataset.service;
    b.classList.toggle("on", !!s[k]);
  });
}
async function toggleService(btn) {
  let service = btn.dataset.service,
    action = btn.classList.contains("on") ? "stop" : "start";
  await fetch(`/api/launcher/${service}/${action}`, { method: "POST" });
  setTimeout(launcherStatus, 500);
}
document.addEventListener("DOMContentLoaded", () => {
  if (window.HOME_POLL) {
    pollHome();
    setInterval(pollHome, 5000);
  }
  if (window.TABLE_KIND) {
    loadTable();
  }
  if (window.LAUNCHER) {
    launcherStatus();
    setInterval(launcherStatus, 3000);
    document
      .querySelectorAll(".form-switch-btn")
      .forEach((b) => (b.onclick = () => toggleService(b)));
  }
});
