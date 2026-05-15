let currentStatus = "",
  sortState = { col: null, dir: 1 },
  tableData = { columns: [], rows: [] },
  selectedTicket = null;

let currentPage = 1;
const ROWS_PER_PAGE = 20;

const COLUMN_NAMES = {
  id: "ID",
  usuario: "Usuario",
  chat_id: "Chat ID",
  asignado_a: "TI Asignado",
  area: "Área",
  descripcion: "Descripción",
  estado: "Estado",
  fecha_creacion: "Creación",
  observacion: "Observación TI",
  fecha_actualizacion: "Actualización",
};

const USER_COLUMN_NAMES = {
  id: "ID",
  nombre: "Nombre TI",
  telegram_id: "Telegram ID",
  creado: "Creado",
};

const SEARCH_ALIASES = {
  id: "id",
  usuario: "usuario",
  chat: "chat_id",
  chat_id: "chat_id",
  asignado: "asignado_a",
  ti: "asignado_a",
  area: "area",
  área: "area",
  descripcion: "descripcion",
  descripción: "descripcion",
  estado: "estado",
  creacion: "fecha_creacion",
  creación: "fecha_creacion",
  observacion: "observacion",
  observación: "observacion",
  actualizacion: "fecha_actualizacion",
  actualización: "fecha_actualizacion",

  nombre: "nombre",
  nombre_ti: "nombre",
  telegram: "telegram_id",
  telegram_id: "telegram_id",
  creado: "creado",
};

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
    `<div id="${id}" class="toast ${bg}" role="alert">
      <div class="d-flex">
        <div class="toast-body">${msg}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`,
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
  ) {
    location.href = "/logout";
  }
}

async function stats() {
  return await (await fetch("/api/stats")).json();
}

async function pollHome() {
  let last = +(sessionStorage.getItem("lastTickets") || 0);
  let s = await stats();
  let bt = document.getElementById("badge-tickets");

  if (s.tickets_new > 0 && bt) {
    bt.textContent = s.tickets_new;
    bt.classList.remove("hidden");
  }

  if (+s.tickets_new > last) {
    showToast(`Hay ${s.tickets_new} tickets nuevos`, "success");
  }

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
    search: "",
    status: currentStatus,
  });

  const data = await (await fetch(`/api/table/${kind}?${q}`)).json();
  tableData = data;

  currentPage = 1;
  renderTable(kind);

  if (kind === "tickets") {
    let s = await stats();

    ["total", "abiertos", "proceso", "cerrados"].forEach((id) => {
      let e = document.getElementById(id);
      if (e) e.textContent = s[id] || 0;
    });
  }
}

function normalizeText(value) {
  return String(value ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function searchableValue(key, value) {
  const k = String(key).toLowerCase();

  if (
    k.includes("fecha") ||
    k.includes("created") ||
    k.includes("updated") ||
    k.includes("creacion") ||
    k.includes("actualizacion")
  ) {
    return `${normalizeText(value)} ${normalizeText(formatDate(value))}`;
  }

  return normalizeText(value);
}

function parseSearchQuery(query) {
  const parts = query
    .split(";")
    .map((p) => p.trim())
    .filter(Boolean);

  const filters = [];
  const global = [];

  for (const part of parts) {
    const match = part.match(/^([\wáéíóúÁÉÍÓÚñÑ_ ]+)\s*:\s*(.+)$/);

    if (!match) {
      global.push(normalizeText(part));
      continue;
    }

    const rawKey = normalizeText(match[1]).replace(/\s+/g, "_");

    const value = normalizeText(match[2]);

    const column = SEARCH_ALIASES[rawKey];

    if (!column) {
      global.push(normalizeText(part));
      continue;
    }

    filters.push({
      column,
      values: value
        .split(",")
        .map((v) => normalizeText(v))
        .filter(Boolean),
    });
  }

  return {
    filters,
    global,
  };
}

function applyAdvancedSearch(rows) {
  const input = document.getElementById("search");
  const query = input?.value || "";

  if (!query.trim()) return rows;

  const parsed = parseSearchQuery(query);

  return rows.filter((row) => {
    const filtersOk = parsed.filters.every((f) => {
      return f.values.some(v =>
  searchableValue(
    f.column,
    row[f.column]
  ).includes(v)
);
    });

    if (!filtersOk) return false;

    const globalOk = parsed.global.every((g) => {
      return Object.entries(row).some(([key, value]) => {
        if (key === "_rowid") return false;

        return searchableValue(key, value).includes(g);
      });
    });

    return globalOk;
  });
}

function renderTable(kind) {
  const t = document.getElementById("data-table");
  if (!t) return;

  let cols = tableData.columns || [];
  let allRows = [...(tableData.rows || [])];
  allRows = applyAdvancedSearch(allRows);
  const visibleCols =
    kind === "tickets"
      ? cols.filter((c) => COLUMN_NAMES[c])
      : cols.filter((c) => USER_COLUMN_NAMES[c]);

  if (sortState.col) {
    allRows.sort(
      (a, b) =>
        String(a[sortState.col] ?? "").localeCompare(
          String(b[sortState.col] ?? ""),
          undefined,
          { numeric: true, sensitivity: "base" },
        ) * sortState.dir,
    );
  }

  const totalPages = Math.max(1, Math.ceil(allRows.length / ROWS_PER_PAGE));

  if (currentPage > totalPages) {
    currentPage = totalPages;
  }

  const start = (currentPage - 1) * ROWS_PER_PAGE;
  const end = start + ROWS_PER_PAGE;
  const rows = allRows.slice(start, end);

  if (!allRows.length) {
    t.innerHTML =
      '<tbody><tr><td class="text-center text-muted py-5">Sin registros para mostrar</td></tr></tbody>';
    renderPagination(1);
    return;
  }

  let head = "<thead><tr>";

  if (kind === "users") head += "<th>Seleccionar</th>";

  head += visibleCols
    .map((c) => {
      const title = kind === "tickets" ? COLUMN_NAMES[c] : USER_COLUMN_NAMES[c];

      return `<th role="button" onclick="sortBy('${String(c).replaceAll("'", "\\'")}')">
        ${title}
        <i class="bi bi-arrow-down-up small opacity-50"></i>
      </th>`;
    })
    .join("");

  if (kind === "tickets") head += "<th></th>";

  head += "</tr></thead>";

  let body =
    "<tbody>" +
    rows
      .map((row) => {
        let tr = `<tr class="${kind === "tickets" ? rowClass(row) : ""}">`;

        if (kind === "users") {
          tr += `<td><input class="form-check-input user-check" type="checkbox" value="${getTelegramId(row)}"></td>`;
        }

        tr += visibleCols
          .map((c) => {
            let value = row[c] ?? "";

            if (
              c.toLowerCase().includes("fecha") ||
              c.toLowerCase().includes("created") ||
              c.toLowerCase().includes("updated") ||
              c.toLowerCase().includes("creacion") ||
              c.toLowerCase().includes("actualizacion") ||
              c.toLowerCase().includes("creado")
            ) {
              value = formatDate(value);
            }

            return `<td>${escapeHtml(value)}</td>`;
          })
          .join("");

        if (kind === "tickets") {
          tr += `
            <td class="text-center">
              <button
                class="btn btn-dark btn-sm rounded-circle option-btn"
                onclick='openTicket(${JSON.stringify(row).replaceAll("'", "&#39;")})'
                title="Editar ticket"
              >
                <i class="bi bi-pencil-square"></i>
              </button>
            </td>`;
        }

        return tr + "</tr>";
      })
      .join("") +
    "</tbody>";

  t.innerHTML = head + body;
  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const container = document.getElementById("table-pagination");
  if (!container) return;

  if (totalPages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = `
    <nav>
      <ul class="pagination justify-content-center mt-4">
        <li class="page-item ${currentPage === 1 ? "disabled" : ""}">
          <button class="page-link" onclick="changePage(${currentPage - 1})">
            Anterior
          </button>
        </li>
  `;

  for (let i = 1; i <= totalPages; i++) {
    html += `
      <li class="page-item ${currentPage === i ? "active" : ""}">
        <button class="page-link" onclick="changePage(${i})">
          ${i}
        </button>
      </li>
    `;
  }

  html += `
        <li class="page-item ${currentPage === totalPages ? "disabled" : ""}">
          <button class="page-link" onclick="changePage(${currentPage + 1})">
            Siguiente
          </button>
        </li>
      </ul>
    </nav>
  `;

  container.innerHTML = html;
}

function changePage(page) {
  const totalPages = Math.max(
    1,
    Math.ceil((tableData.rows || []).length / ROWS_PER_PAGE),
  );

  if (page < 1 || page > totalPages) return;

  currentPage = page;
  renderTable(window.TABLE_KIND || "tickets");
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
  currentPage = 1;
  renderTable(window.TABLE_KIND || "tickets");
}

function setStatusFilter(v, btn) {
  currentStatus = v;

  document
    .querySelectorAll(".stat-card")
    .forEach((b) => b.classList.remove("active"));

  btn.classList.add("active");
  currentPage = 1;
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

  currentPage = 1;
  loadTable();
}

async function openTicket(row) {
  selectedTicket = row;

  const form = document.getElementById("ticketForm");
  form.innerHTML = "";

  const estadoActual = String(row.estado || "").trim();
  const isClosed = estadoActual.toLowerCase() === "cerrado";

  let tiUsers = [];

  try {
    const r = await fetch("/api/ti-users");
    tiUsers = await r.json();
  } catch (e) {
    tiUsers = [];
  }

  const plainFields = [
    ["id", "ID"],
    ["usuario", "Usuario"],
    ["chat_id", "Chat ID"],
    ["area", "Área"],
    ["descripcion", "Descripción"],
    ["fecha_creacion", "Creación"],
    ["fecha_actualizacion", "Actualización"],
  ];

  plainFields.forEach(([key, label]) => {
    let value = row[key] ?? "-";

    if (key.includes("fecha")) {
      value = formatDate(value);
    }

    form.insertAdjacentHTML(
      "beforeend",
      `<div class="col-md-6">
        <label class="form-label fw-semibold text-primary">${label}</label>
        <div class="detail-plain">${escapeHtml(value)}</div>
      </div>`,
    );
  });

  form.insertAdjacentHTML(
    "beforeend",
    `<div class="col-md-6">
      <label class="form-label fw-semibold text-primary">TI Asignado</label>
      <select class="form-select" name="asignado_a" ${isClosed ? "disabled" : ""}>
        <option value="">No asignar</option>
        ${tiUsers
          .map((u) => {
            const nombre = escapeHtml(u.nombre || "");
            const selected =
              String(row.asignado_a || "") === String(u.nombre || "")
                ? "selected"
                : "";

            return `<option value="${nombre}" ${selected}>${nombre}</option>`;
          })
          .join("")}
      </select>
    </div>`,
  );

  form.insertAdjacentHTML(
    "beforeend",
    `<div class="col-md-6">
      <label class="form-label fw-semibold text-primary">Estado</label>
      <select class="form-select estado-select" name="estado" ${isClosed ? "disabled" : ""}>
        <option value="Abierto" ${estadoActual === "Abierto" ? "selected" : ""}>🟢 Abierto</option>
        <option value="En proceso" ${estadoActual === "En Proceso" ? "selected" : ""}>🟡 En proceso</option>
        <option value="Cerrado" ${estadoActual === "Cerrado" ? "selected" : ""}>🔴 Cerrado</option>
      </select>
    </div>`,
  );

  form.insertAdjacentHTML(
    "beforeend",
    `<div class="col-12">
      <label class="form-label fw-semibold text-primary">Observación TI</label>
      <textarea
        class="form-control"
        rows="4"
        name="observacion"
        ${isClosed ? "readonly" : ""}
      >${escapeHtml(row.observacion || "")}</textarea>
    </div>`,
  );

  if (isClosed) {
    form.insertAdjacentHTML(
      "afterbegin",
      `<div class="col-12">
        <div class="alert alert-secondary">
          Este ticket está cerrado. No se pueden realizar cambios.
        </div>
      </div>`,
    );
  }

  const saveBtn = document.getElementById("saveTicketBtn");
  if (saveBtn) {
    saveBtn.disabled = isClosed;
  }

  new bootstrap.Modal("#ticketModal").show();
}

async function saveTicket() {
  if (!selectedTicket) return;

  if (String(selectedTicket.estado || "").toLowerCase() === "cerrado") {
    showToast("No se puede editar un ticket cerrado", "warning");
    return;
  }

  const form = document.getElementById("ticketForm");

  const estado = form.querySelector('[name="estado"]')?.value || "";
  const asignado = form.querySelector('[name="asignado_a"]')?.value || "";
  const observacion = form.querySelector('[name="observacion"]')?.value || "";

  if (["En proceso", "Cerrado"].includes(estado) && !asignado.trim()) {
    showToast("Para dejar el ticket En proceso o Cerrado debes asignar un TI", "warning");
    return;
  }

  if (estado === "Cerrado" && !observacion.trim()) {
    showToast("Para cerrar el ticket debes ingresar una observación TI", "warning");
    return;
  }

  const body = {
    estado,
    asignado_a: asignado,
    observacion,
  };

  if (
    !(await confirmBox(
      "Guardar cambios",
      "¿Deseas guardar los cambios de este ticket?",
      "Guardar",
    ))
  )
    return;

  const r = await fetch(`/api/tickets/${selectedTicket._rowid}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const j = await r.json().catch(() => ({}));

  showToast(
    r.ok ? "Ticket actualizado correctamente" : j.msg || "No se pudo actualizar",
    r.ok ? "success" : "danger",
  );

  if (r.ok) {
    bootstrap.Modal.getInstance(document.getElementById("ticketModal")).hide();
    loadTable();
  }
}

function getFilteredRowsForExport() {
  let rows = [...(tableData.rows || [])];

  rows = applyAdvancedSearch(rows);

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

  return rows;
}

async function exportTicketsExcel() {
  const rows = getFilteredRowsForExport();

  const r = await fetch("/api/export/tickets", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ rows }),
  });

  if (!r.ok) {
    showToast("No se pudo generar el Excel", "danger");
    return;
  }

  const blob = await r.blob();
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "reporte_tickets.xlsx";
  a.click();

  URL.revokeObjectURL(url);
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

  const rows = getFilteredRowsForExport();

  const r = await fetch("/api/email/tickets", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ rows }),
  });

  const j = await r.json().catch(() => ({}));

  showToast(
    r.ok ? "Reporte enviado correctamente" : j.msg || "No se pudo enviar",
    r.ok ? "success" : "danger",
  );
}

function getTelegramId(row) {
  let keys = Object.keys(row);

  let k =
    keys.find((x) =>
      ["telegram_id", "chat_id", "id_telegram", "telegram", "user_id"].includes(
        x.toLowerCase(),
      ),
    ) ||
    keys.find((x) => x.toLowerCase().includes("telegram")) ||
    keys[1] ||
    keys[0];

  return row[k] ?? "";
}

async function addUserFromForm() {
  let id = document.getElementById("newTelegramId").value.trim();
  let nombre = document.getElementById("newTiName").value.trim();

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
  let picked = [...document.querySelectorAll(".user-check:checked")];

  if (!picked.length) {
    showToast("Selecciona uno o más TI para eliminar", "warning");
    return;
  }

  let ids = picked.map((x) => x.value);

  if (
    !(await confirmBox(
      "Eliminar TI",
      `¿Seguro que deseas eliminar ${ids.length} usuario(s) TI seleccionado(s)?`,
      "Eliminar",
    ))
  )
    return;

  const r = await fetch("/api/users", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_ids: ids }),
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
  let service = btn.dataset.service;
  let action = btn.classList.contains("on") ? "stop" : "start";

  await fetch(`/api/launcher/${service}/${action}`, { method: "POST" });
  setTimeout(launcherStatus, 500);
}

async function loadLogs() {
  const r = await fetch("/api/logs");
  const logs = await r.json();

  const worker = document.getElementById("log-worker");
  const webhook = document.getElementById("log-webhook");
  const ngrok = document.getElementById("log-ngrok");
  const panel = document.getElementById("log-panel");

  if (worker) worker.textContent = logs.worker || "";
  if (webhook) webhook.textContent = logs.webhook || "";
  if (ngrok) ngrok.textContent = logs.ngrok || "";
  if (panel) panel.textContent = logs.panel || "";
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

  if (window.LOGS_PAGE) {
    loadLogs();
    setInterval(loadLogs, 3000);
  }
});
