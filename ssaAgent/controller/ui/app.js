const API_BASE = window.location.origin;

function getToken() {
  return window.localStorage.getItem("api_token") || "";
}

function setToken(tok) {
  window.localStorage.setItem("api_token", tok);
}

async function api(path, opts) {
  opts = opts || {};
  opts.headers = opts.headers || {};
  const token = getToken();
  if (token) {
    opts.headers["X-ADMIN-TOKEN"] = token;
  }
  const r = await fetch(API_BASE + path, opts);
  if (!r.ok) {
    const txt = await r.text();
    throw new Error("HTTP " + r.status + ": " + txt);
  }
  return r.json();
}

function log(msg) {
  const out = document.getElementById("out");
  const stamp = new Date().toISOString();
  out.value = `[${stamp}] ${msg}\n` + out.value;
}

function statusClass(status) {
  if (!status) return "pending";
  const s = String(status).toLowerCase();
  if (["approved", "success"].includes(s)) return "approved";
  if (["failed", "denied", "expired"].includes(s)) return "failed";
  return "pending";
}

function updateKpis(workflows) {
  const total = workflows.length;
  const pending = workflows.filter(w => String(w.status).toLowerCase() === "pending").length;
  const approved = workflows.filter(w => String(w.status).toLowerCase() === "approved").length;
  document.getElementById("kpiTotal").innerText = total || "0";
  document.getElementById("kpiPending").innerText = pending || "0";
  document.getElementById("kpiApproved").innerText = approved || "0";
}

async function loadWorkflows() {
  try {
    const data = await api("/api/workflows");
    const tbody = document.querySelector("#workflowsTable tbody");
    tbody.innerHTML = "";
    updateKpis(data);

    for (const wf of data) {
      const tr = document.createElement("tr");
      const statusCls = statusClass(wf.status);

      tr.innerHTML = `
        <td><span class="pill-muted">${(wf.workflow_id || "").slice(0,8)}…</span></td>
        <td><span class="badge-script">${wf.script_id || "-"}</span></td>
        <td><span class="status-pill ${statusCls}">${wf.status || "?"}</span></td>
        <td>${wf.created_at || ""}</td>
        <td style="text-align:right;">
          <button data-id="${wf.workflow_id}" class="btn btn-ghost btn-audit">Audit</button>
          <button data-id="${wf.workflow_id}" class="btn btn-soft btn-exec">Execute</button>
        </td>
      `;
      tbody.appendChild(tr);
    }

  } catch (e) {
    log("ERR loading workflows: " + e.message);
  }
}

async function loadAgents() {
  try {
    const data = await api("/api/agents");
    const tbody = document.querySelector("#agentsTable tbody");
    tbody.innerHTML = "";

    for (const ag of data) {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${ag.agent_name}</td>
        <td>${ag.hostname || ""}</td>
        <td>${ag.port || ""}</td>
        <td>${ag.status || ""}</td>
        <td>${ag.last_seen || ""}</td>
      `;

      tbody.appendChild(tr);
    }

  } catch (e) {
    log("ERR loading agents: " + e.message);
  }
}

async function createWorkflow() {
  const scriptId = document.getElementById("wfScriptId").value.trim();
  const targetsRaw = document.getElementById("wfTargets").value;
  const requestor = document.getElementById("wfRequestor").value.trim() || "admin";
  const reason = document.getElementById("wfReason").value.trim();

  if (!scriptId) {
    alert("Script ID is required");
    return;
  }

  let targets = [];
  try {
    targets = JSON.parse(targetsRaw);
  } catch (e) {
    alert("Invalid JSON for targets");
    return;
  }

  try {
    const body = {
      script_id: scriptId,
      targets,
      required_approval_levels: 1,
      notify_email: null,
      ttl_minutes: 60,
      reason,
      requestor,
    };

    const res = await api("/api/workflows", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    log("Created workflow: " + res.workflow_id);

  } catch (e) {
    log("ERR creating workflow: " + e.message);
  }
}

async function loadScriptsDropdown() {
  try {
    const scripts = await api("/api/scripts/");
    const sel = document.getElementById("wfScriptId");
    sel.innerHTML = `<option value="">-- Select Script --</option>`;
    for (const s of scripts) {
      const opt = document.createElement("option");
      opt.value = s.script_id;
      opt.textContent = `${s.script_id} (${s.description || ""})`;
      sel.appendChild(opt);
    }
  } catch (e) {
    log("ERR loading scripts dropdown: " + e.message);
  }
}

async function loadAgentsDropdown() {
  try {
    const agents = await api("/api/agents/");
    const sel = document.getElementById("wfTargetsDropdown");
    sel.innerHTML = "";
    for (const a of agents) {
      const opt = document.createElement("option");
      opt.value = a.agent_name;
      opt.textContent = `${a.agent_name} (${a.host}:${a.port})`;
      sel.appendChild(opt);
    }
  } catch (e) {
    log("ERR loading agents dropdown: " + e.message);
  }
}


async function handleTableClick(ev) {
  const btn = ev.target;

  if (btn.classList.contains("btn-audit")) {
    const id = btn.getAttribute("data-id");
    try {
      const res = await api("/api/workflows/" + id + "/audit");
      log("Audit for " + id + ": " + JSON.stringify(res.audit, null, 2));
    } catch (e) {
      log("ERR audit: " + e.message);
    }

  } else if (btn.classList.contains("btn-exec")) {
    const id = btn.getAttribute("data-id");
    try {
      const res = await api("/api/workflows/" + id + "/execute", { method: "POST" });
      log("Execute result for " + id + ": " + JSON.stringify(res, null, 2));
      loadWorkflows();
    } catch (e) {
      log("ERR execute: " + e.message);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const tokenInput = document.getElementById("token");
  tokenInput.value = getToken();

  document.getElementById("refreshWorkflows")
    .addEventListener("click", loadWorkflows);

  document.getElementById("refreshAgents")
    .addEventListener("click", loadAgents);

  document.getElementById("createWorkflow")
    .addEventListener("click", createWorkflow);

  document.getElementById("saveToken")
    .addEventListener("click", () => {
      const tok = document.getElementById("token").value.trim();
      setToken(tok);
      log("Token saved. Using as X-ADMIN-TOKEN.");

      // Load once (not twice)
      loadWorkflows();
      loadAgents();
    });

  document.getElementById("clearLog")
    .addEventListener("click", () => {
      document.getElementById("out").value = "";
    });

  document.querySelector("#workflowsTable")
    .addEventListener("click", handleTableClick);

  // Auto-load if token already exists
  if (getToken()) {
    loadWorkflows();
    loadAgents();
  }
});
