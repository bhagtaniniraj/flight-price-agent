/**
 * api.js — Fetch wrapper for all Flight Price Agent API endpoints.
 */

const API_BASE = "";

async function request(method, path, body = null, params = null) {
  let url = API_BASE + path;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    url += "?" + qs;
  }
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== null) {
    options.body = JSON.stringify(body);
  }
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || JSON.stringify(err);
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

// ── Search ──────────────────────────────────────────────────────────────────

export async function searchFlights(payload) {
  return request("POST", "/api/v1/search/", payload);
}

export async function compareFlights(params) {
  return request("GET", "/api/v1/search/compare", null, params);
}

// ── Alerts ──────────────────────────────────────────────────────────────────

export async function createAlert(payload) {
  return request("POST", "/api/v1/alerts/", payload);
}

export async function listAlerts() {
  return request("GET", "/api/v1/alerts/");
}

export async function getAlert(id) {
  return request("GET", `/api/v1/alerts/${id}`);
}

export async function updateAlert(id, payload) {
  return request("PATCH", `/api/v1/alerts/${id}`, payload);
}

export async function deleteAlert(id) {
  return request("DELETE", `/api/v1/alerts/${id}`);
}

// ── Predictions ──────────────────────────────────────────────────────────────

export async function predictPrice(payload) {
  return request("POST", "/api/v1/predict/", payload);
}

// ── Health ───────────────────────────────────────────────────────────────────

export async function health() {
  return request("GET", "/health");
}
