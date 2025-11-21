// ===============================
// ORC PRO – Unified app.js
// ===============================

const API_BASE = window.location.origin;

// -------------------------------
// TOKEN HELPERS
// -------------------------------
function getToken() {
  const tok = localStorage.getItem("api_token");
  return tok || "";
}

function setToken(tok) {
  localStorage.setItem("api_token", tok);
}

// -------------------------------
// API WRAPPER
// -------------------------------
async function api(path, opts = {}) {
  opts.headers = opts.headers || {};

  const token = getToken();
  if (token) {
    opts.headers["X-ADMIN-TOKEN"] = token;
  }

  const r = await fetch(API_BASE + path, opts);

  // Do NOT spam the UI with 422 on first load
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`HTTP ${r.status}: ${txt}`);
  }
  return r.json();
}

// -------------------------------
// LOGGING
// -------------------------------
function log(msg) {
  const out = document.getElementById("out");
  if (!out) return;
  const stamp = new Date().toISOString();
  out.value = `[${stamp}] ${msg}\n` + out.value;
}

// -------------------------------
// STATUS COLOR MAPPING
// -------------------------------
function statusClass(status) {
  if (!status) return "pending";
  const s = String(status).toLowerCase();
  if (["approved", "success"].includes(s)) return "approved";
  if (["failed", "denied", "expired"].includes(s)) return "failed";
  return "pending";
}

// -------------------------------
// KPI UPDATES
// -------------------------------
function updateKpis(w) {
  document.getElementById("kpiTotal").innerText = w.length;
  document.getElementById("kpiPending").innerText =
    w.filter(x => x.status?.toLowerCase() === "pending").length;
  document.getElementById("kpiApproved").innerText =
    w.filter(x => x.status?.toLowerCase() === "approved").length;
}

// -------------------------------
// LOAD WORKFLOWS
// -------------------------------
async function loadWorkflows() {
  try {
    const data = await api("/api/workflows/");
    updateKpis(data);

    const tbody = document.querySelector("#workflowsTable tbody");
    tbody.innerHTML = "";

    data.forEach(wf => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="pill-muted">${(wf.workflow_id || "").slice(0, 8)}…</span></td>
        <td><span class="badge-script">${wf.script_id || "-"}</span></td>
        <td><span class="status-pill ${statusClass(wf.status)}">${wf.status}</span></td>
        <td>${wf.created_at || ""}</td>
        <td style="text-align:right;">
          <button class="btn btn-ghost btn-audit" data-id="${wf.workflow_id}">Audit</button>
          <button class="btn btn-soft btn-exec" data-id="${wf.workflow_id}">Execute</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    log("Loaded workflows.");
  } catch (e) {
    if (!e.message.includes("401")) log("ERR loading workflows: " + e.message);
  }
}

// -------------------------------
// LOAD AGENTS
// -------------------------------
async function loadAgents() {
  try {
    const data = await api("/api/agents/");
    const tbody = document.querySelector("#agentsTable tbody");
    tbody.innerHTML = "";

    data.forEach(ag => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${ag.agent_name}</td>
        <td>${ag.host}</td>
        <td>${ag.port}</td>
        <td>${ag.status}</td>
        <td>${ag.last_seen}</td>
      `;
      tbody.appendChild(tr);
    });

    log("Loaded agents.");
  } catch (e) {
    if (!e.message.includes("401")) log("ERR loading agents: " + e.message);
  }
}

// -------------------------------
// CREATE WORKFLOW
// -------------------------------
async function createWorkflow() {
  const scriptId = document.getElementById("wfScriptId").value.trim();
  const requestor = document.getElementById("wfRequestor").value.trim();
  const reason = document.getElementById("wfReason").value.trim();
  const targetsRaw = document.getElementById("wfTargets").value;

  if (!scriptId) return alert("Script required.");

  let targets = [];
  try { targets = JSON.parse(targetsRaw); }
  catch { return alert("Targets must be valid JSON."); }

  try {
    const body = {
      script_id: scriptId,
      targets,
      requestor,
      reason,
      required_approval_levels: 1,
      ttl_minutes: 60
    };

    const r = await api("/api/workflows/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    log("Workflow created: " + r.workflow_id);
    loadWorkflows();

  } catch (e) {
    log("ERR creating workflow: " + e.message);
  }
}

// -------------------------------
// TABLE BUTTON ACTIONS
// -------------------------------
async function handleTableClick(ev) {
  const btn = ev.target;
  if (!btn.dataset.id) return;

  const wid = btn.dataset.id;

  if (btn.classList.contains("btn-audit")) {
    try {
      const r = await api(`/api/workflows/${wid}/audit`);
      log("Audit " + wid + ":\n" + JSON.stringify(r.audit, null, 2));
    } catch (e) {
      log("ERR audit: " + e.message);
    }
  }

  if (btn.classList.contains("btn-exec")) {
    try {
      const r = await api(`/api/workflows/${wid}/execute`, { method: "POST" });
      log("EXEC result: " + JSON.stringify(r, null, 2));
      loadWorkflows();
    } catch (e) {
      log("ERR execute: " + e.message);
    }
  }
}

// -------------------------------
// DROPDOWNS
// -------------------------------
async function loadScriptsDropdown() {
  try {
    const scripts = await api("/api/scripts/");
    const sel = document.getElementById("wfScriptId");
    sel.innerHTML = `<option value="">-- select script --</option>`;
    scripts.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.script_id;
      opt.textContent = `${s.script_id} (${s.description})`;
      sel.appendChild(opt);
    });
  } catch (e) {
    log("ERR dropdown_scripts: " + e.message);
  }
}

// -------------------------------
// INIT
// -------------------------------
document.addEventListener("DOMContentLoaded", () => {

  // preload saved token
  const tokenInput = document.getElementById("token");
  tokenInput.value = getToken();

  document.getElementById("saveToken").addEventListener("click", () => {
    const tok = tokenInput.value.trim();
    setToken(tok);
    log("Token saved.");
    setTimeout(() => window.location.reload(), 300);
  });

  document.getElementById("refreshWorkflows").addEventListener("click", loadWorkflows);
  document.getElementById("refreshAgents").addEventListener("click", loadAgents);
  document.getElementById("createWorkflow").addEventListener("click", createWorkflow);

  document.getElementById("workflowsTable").addEventListener("click", handleTableClick);

  document.getElementById("clearLog").addEventListener("click", () => {
    document.getElementById("out").value = "";
  });

  loadScriptsDropdown();

  // auto load if token already saved
  if (getToken()) {
    loadWorkflows();
    loadAgents();
  }
});
