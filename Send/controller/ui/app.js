const API_BASE = window.location.origin;

function getToken() {
  const tok = window.localStorage.getItem("api_token");
  console.log("DEBUG: getToken ->", tok);
  return tok || "";
}

function setToken(tok) {
  console.log("DEBUG: setToken ->", tok);
  window.localStorage.setItem("api_token", tok);
}

async function api(path, opts) {
  opts = opts || {};
  opts.headers = opts.headers || {};

  const token = getToken();
  if (token && token.length > 0) {
    opts.headers["X-ADMIN-TOKEN"] = token;
    console.log("DEBUG: attaching X-ADMIN-TOKEN:", token);
  } else {
    console.log("DEBUG: NO TOKEN available in localStorage");
  }

  const r = await fetch(API_BASE + path, opts);
  if (!r.ok) {
    const txt = await r.text();
    throw new Error("HTTP " + r.status + ": " + txt);
  }
  return r.json();
}

// ======================================================
// UI LOGIC
// ======================================================

function log(msg) {
  const out = document.getElementById("out");
  const stamp = new Date().toISOString();
  out.value = `[${stamp}] ${msg}\n` + out.value;
}

async function loadWorkflows() {
  try {
    const data = await api("/api/workflows/");
    log("Loaded workflows OK");
  } catch (e) {
    log("ERR loading workflows: " + e.message);
  }
}

async function loadAgents() {
  try {
    const data = await api("/api/agents/");
    log("Loaded agents OK");
  } catch (e) {
    log("ERR loading agents: " + e.message);
  }
}

// ======================================================
// EVENT BINDINGS
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
  const tokenInput = document.getElementById("token");

  // preload stored token in UI
  tokenInput.value = getToken();

  document.getElementById("saveToken").addEventListener("click", () => {
    const tok = tokenInput.value.trim();
    setToken(tok);
    log("Token saved. Reloading...");
    setTimeout(() => window.location.reload(), 500);
  });

  document.getElementById("refreshWorkflows").addEventListener("click", loadWorkflows);
  document.getElementById("refreshAgents").addEventListener("click", loadAgents);

  // auto load on startup if token is present
  if (getToken()) {
    loadWorkflows();
    loadAgents();
  }
});
