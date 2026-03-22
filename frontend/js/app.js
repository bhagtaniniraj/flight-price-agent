/**
 * app.js — Main application logic, DOM manipulation, event handlers.
 */
import * as API from "./api.js";

// ── Section navigation ────────────────────────────────────────────────────

const sections = document.querySelectorAll(".section");
const navTabs  = document.querySelectorAll(".nav-tab");

function showSection(id) {
  sections.forEach(s => s.classList.toggle("active", s.id === id));
  navTabs.forEach(t => t.classList.toggle("active", t.dataset.section === id));
}

navTabs.forEach(tab => {
  tab.addEventListener("click", () => showSection(tab.dataset.section));
});

// ── Toast notifications ───────────────────────────────────────────────────

const toastContainer = document.getElementById("toast-container");

function showToast(msg, type = "info") {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ── Health check ──────────────────────────────────────────────────────────

const healthDot = document.getElementById("health-dot");

async function checkHealth() {
  try {
    await API.health();
    healthDot.className = "health-dot ok";
    healthDot.title = "API healthy";
  } catch {
    healthDot.className = "health-dot err";
    healthDot.title = "API unreachable";
  }
}
checkHealth();

// ── Helpers ──────────────────────────────────────────────────────────────

function fmtTime(iso) {
  if (!iso) return "–";
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch { return iso; }
}

function fmtDate(iso) {
  if (!iso) return "–";
  try {
    return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
  } catch { return iso; }
}

function providerClass(source) {
  const map = { amadeus: "provider-amadeus", kiwi: "provider-kiwi", duffel: "provider-duffel" };
  return map[source?.toLowerCase()] || "provider-default";
}

function setLoading(btn, loading) {
  if (loading) {
    btn.disabled = true;
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> Searching…`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
  }
}

function validateIATA(code) {
  return /^[A-Za-z]{3}$/.test(code);
}

function markError(input, msg) {
  input.classList.add("error");
  input.title = msg;
}

function clearErrors(...inputs) {
  inputs.forEach(i => { i.classList.remove("error"); i.title = ""; });
}

function skeletonCards(count = 3) {
  return Array.from({ length: count },
    () => `<div class="skeleton skeleton-card"></div>`).join("");
}

// ═══════════════════════════════════════════════════════════════════════════
// SECTION 1 — FLIGHT SEARCH
// ═══════════════════════════════════════════════════════════════════════════

const searchForm   = document.getElementById("search-form");
const originInput  = document.getElementById("origin");
const destInput    = document.getElementById("destination");
const swapBtn      = document.getElementById("swap-btn");
const searchBtn    = document.getElementById("search-btn");
const resultsArea  = document.getElementById("results-area");
const resultsBar   = document.getElementById("results-bar");
const flightsGrid  = document.getElementById("flights-grid");
const sortSelect   = document.getElementById("sort-select");

let currentOffers = [];

// Swap origin ↔ destination
swapBtn.addEventListener("click", () => {
  [originInput.value, destInput.value] = [destInput.value, originInput.value];
});

// Auto-uppercase airport codes
[originInput, destInput].forEach(inp => {
  inp.addEventListener("input", () => { inp.value = inp.value.toUpperCase(); });
});

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const origin   = originInput.value.trim().toUpperCase();
  const dest     = destInput.value.trim().toUpperCase();
  const depDate  = document.getElementById("departure-date").value;
  const retDate  = document.getElementById("return-date").value || null;
  const adults   = parseInt(document.getElementById("adults").value);
  const currency = document.getElementById("currency").value;
  const maxRes   = parseInt(document.getElementById("max-results").value);

  clearErrors(originInput, destInput);
  let valid = true;
  if (!validateIATA(origin))  { markError(originInput, "Enter a 3-letter IATA code"); valid = false; }
  if (!validateIATA(dest))    { markError(destInput,   "Enter a 3-letter IATA code"); valid = false; }
  if (!depDate)               { showToast("Please select a departure date", "error"); valid = false; }
  if (!valid) return;

  setLoading(searchBtn, true);
  resultsBar.classList.add("hidden");
  flightsGrid.innerHTML = skeletonCards(4);
  resultsArea.classList.remove("hidden");

  try {
    const payload = { origin, destination: dest, departure_date: depDate,
                      return_date: retDate, adults, currency, max_results: maxRes };
    const data = await API.searchFlights(payload);
    currentOffers = data.offers || [];
    renderResults(data, currency);
    showToast(`Found ${data.total_results} flights`, "success");
  } catch (err) {
    flightsGrid.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>${err.message}</p></div>`;
    showToast(err.message, "error");
  } finally {
    setLoading(searchBtn, false);
  }
});

function renderResults(data, searchCurrency) {
  const offers = data.offers || [];
  const currency = searchCurrency || offers[0]?.currency || "";

  // Summary bar
  resultsBar.classList.remove("hidden");
  document.getElementById("total-results").textContent = data.total_results;
  document.getElementById("cheapest-price").textContent =
    data.cheapest_price != null
      ? `${currency} ${data.cheapest_price.toFixed(2)}`
      : "–";
  const provList = document.getElementById("providers-queried");
  provList.innerHTML = `<strong>Providers:</strong> ` +
    (data.providers_queried || []).map(p =>
      `<span class="provider-badge ${providerClass(p)}">${p}</span>`
    ).join("");

  sortAndRender(offers);
}

sortSelect.addEventListener("change", () => sortAndRender(currentOffers));

function sortAndRender(offers) {
  let sorted = [...offers];
  if (sortSelect.value === "price-asc")  sorted.sort((a, b) => a.price - b.price);
  if (sortSelect.value === "price-desc") sorted.sort((a, b) => b.price - a.price);

  if (!sorted.length) {
    flightsGrid.innerHTML = `<div class="empty-state"><div class="empty-icon">✈️</div><p>No flights found for this route. Try different dates or airports.</p></div>`;
    return;
  }
  flightsGrid.innerHTML = sorted.map(renderFlightCard).join("");
}

function renderFlightCard(offer) {
  const seg0   = offer.segments?.[0] || {};
  const segN   = offer.segments?.[offer.segments.length - 1] || {};
  const stops  = offer.segments?.length > 1 ? `${offer.segments.length - 1} stop(s)` : "Non-stop";
  const depTime = fmtTime(seg0.departure_time);
  const arrTime = fmtTime(segN.arrival_time);
  const primaryAirline = (offer.airline_codes?.[0] || seg0.carrier_code || "–").trim();
  const allAirlines = (offer.airline_codes || [seg0.carrier_code]).filter(Boolean).join(", ") || "–";
  const linkEl = offer.deep_link
    ? `<a class="book-btn" href="${offer.deep_link}" target="_blank" rel="noopener">Book →</a>`
    : `<span class="book-btn" style="opacity:.5;cursor:default">No Link</span>`;

  return `
  <div class="flight-card${offer.is_deal ? " deal" : ""}">
    <div class="airline-code">${primaryAirline}</div>
    <div class="flight-info">
      <div class="route-times">
        <span>${depTime}</span>
        <span class="route-arrow">──✈──</span>
        <span>${arrTime}</span>
      </div>
      <div class="flight-meta">
        <span>🕐 ${offer.total_duration || "–"}</span>
        <span>🔁 ${stops}</span>
        ${offer.bags_included > 0 ? `<span>🧳 ${offer.bags_included} bag(s)</span>` : ""}
        <span><span class="provider-badge ${providerClass(offer.source)}">${offer.source || "–"}</span></span>
        ${offer.is_deal ? `<span class="deal-badge">🏷 DEAL</span>` : ""}
      </div>
    </div>
    <div class="price-col">
      <div class="price-currency">${offer.currency}</div>
      <div class="price-amount">${offer.price.toFixed(2)}</div>
      ${linkEl}
    </div>
  </div>`;
}

// ═══════════════════════════════════════════════════════════════════════════
// SECTION 2 — PRICE PREDICTION
// ═══════════════════════════════════════════════════════════════════════════

const predictForm   = document.getElementById("predict-form");
const predictBtn    = document.getElementById("predict-btn");
const predictResult = document.getElementById("predict-result");

// Auto-uppercase
["pred-origin", "pred-destination"].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("input", () => { el.value = el.value.toUpperCase(); });
});

predictForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const origin   = document.getElementById("pred-origin").value.trim().toUpperCase();
  const dest     = document.getElementById("pred-destination").value.trim().toUpperCase();
  const depDate  = document.getElementById("pred-dep-date").value;
  const days     = parseInt(document.getElementById("pred-days").value);
  const price    = parseFloat(document.getElementById("pred-price").value);
  const adults   = parseInt(document.getElementById("pred-adults").value);

  if (!validateIATA(origin) || !validateIATA(dest)) {
    showToast("Enter valid 3-letter airport codes", "error"); return;
  }
  if (!depDate) { showToast("Select a departure date", "error"); return; }

  predictBtn.disabled = true;
  predictBtn.innerHTML = `<span class="spinner"></span> Predicting…`;
  predictResult.classList.add("hidden");

  try {
    const data = await API.predictPrice({ origin, destination: dest,
      departure_date: depDate, days_until_departure: days,
      current_price: price, adults });
    renderPrediction(data);
    showToast("Prediction ready", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    predictBtn.disabled = false;
    predictBtn.innerHTML = "🔮 Predict Price";
  }
});

function renderPrediction(d) {
  const diff = d.predicted_price - d.current_price;
  const arrowClass = diff > 0.5 ? "up" : diff < -0.5 ? "down" : "same";
  const arrowIcon  = diff > 0.5 ? "📈" : diff < -0.5 ? "📉" : "➡️";

  const recMap = {
    buy_now:   { cls: "rec-buy",  label: "✅ BUY NOW" },
    wait:      { cls: "rec-wait", label: "⏳ WAIT" },
    good_deal: { cls: "rec-deal", label: "💎 GOOD DEAL" },
  };
  const rec = recMap[d.recommendation] || { cls: "rec-deal", label: d.recommendation };

  const trendIcon = { rising: "📈", falling: "📉", stable: "➡️" };
  const confPct   = Math.round((d.confidence || 0) * 100);

  document.getElementById("pred-result-content").innerHTML = `
    <h3>Prediction for ${d.origin} → ${d.destination} on ${d.departure_date}</h3>
    <div class="pred-prices">
      <div class="pred-price-item">
        <div class="pred-price-label">Current Price</div>
        <div class="pred-price-value">$${d.current_price.toFixed(2)}</div>
      </div>
      <div class="pred-arrow ${arrowClass}">${arrowIcon}</div>
      <div class="pred-price-item">
        <div class="pred-price-label">Predicted Price</div>
        <div class="pred-price-value">$${d.predicted_price.toFixed(2)}</div>
      </div>
    </div>
    <div>
      <span class="rec-badge ${rec.cls}">${rec.label}</span>
    </div>
    <div class="confidence-bar-wrap mt-2">
      <div class="confidence-label">
        <span>Model Confidence</span><span>${confPct}%</span>
      </div>
      <div class="confidence-bar">
        <div class="confidence-fill" style="width:${confPct}%"></div>
      </div>
    </div>
    <div class="trend-row mt-1">
      <span>${trendIcon[d.price_trend] || "➡️"}</span>
      <span>Price trend: <strong>${d.price_trend}</strong></span>
      <span style="color:var(--gray-400)">|</span>
      <span>${d.days_until_departure} day(s) until departure</span>
    </div>
  `;
  predictResult.classList.remove("hidden");
}

// ═══════════════════════════════════════════════════════════════════════════
// SECTION 3 — PRICE ALERTS
// ═══════════════════════════════════════════════════════════════════════════

const alertForm  = document.getElementById("alert-form");
const alertBtn   = document.getElementById("alert-btn");
const alertsBody = document.getElementById("alerts-tbody");

// Auto-uppercase
["alert-origin", "alert-destination"].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("input", () => { el.value = el.value.toUpperCase(); });
});

async function loadAlerts() {
  alertsBody.innerHTML = `<tr><td colspan="7" class="text-center">${skeletonCards(1)}</td></tr>`;
  try {
    const alerts = await API.listAlerts();
    renderAlerts(alerts);
  } catch (err) {
    alertsBody.innerHTML = `<tr><td colspan="7" class="text-center" style="color:var(--red)">Failed to load alerts: ${err.message}</td></tr>`;
  }
}

function renderAlerts(alerts) {
  if (!alerts || !alerts.length) {
    alertsBody.innerHTML = `<tr><td colspan="7" class="text-center" style="color:var(--gray-400);padding:2rem">No alerts yet. Create one above!</td></tr>`;
    return;
  }
  alertsBody.innerHTML = alerts.map(a => {
    const statusCls = a.triggered_at ? "status-triggered" : a.is_active ? "status-active" : "status-inactive";
    const statusTxt = a.triggered_at ? "Triggered" : a.is_active ? "Active" : "Inactive";
    return `
    <tr>
      <td><strong>${a.origin} → ${a.destination}</strong></td>
      <td>${a.departure_date}</td>
      <td><strong>${a.currency} ${a.target_price.toFixed(2)}</strong></td>
      <td>${a.email || "–"}</td>
      <td><span class="status-badge ${statusCls}">${statusTxt}</span></td>
      <td>${fmtDate(a.created_at)}</td>
      <td><button class="del-btn" data-id="${a.id}">🗑 Delete</button></td>
    </tr>`;
  }).join("");

  // Bind delete buttons
  alertsBody.querySelectorAll(".del-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this alert?")) return;
      try {
        await API.deleteAlert(btn.dataset.id);
        showToast("Alert deleted", "success");
        loadAlerts();
      } catch (err) {
        showToast("Failed to delete: " + err.message, "error");
      }
    });
  });
}

alertForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const origin   = document.getElementById("alert-origin").value.trim().toUpperCase();
  const dest     = document.getElementById("alert-destination").value.trim().toUpperCase();
  const depDate  = document.getElementById("alert-dep-date").value;
  const targetP  = parseFloat(document.getElementById("alert-price").value);
  const currency = document.getElementById("alert-currency").value;
  const email    = document.getElementById("alert-email").value.trim() || null;

  if (!validateIATA(origin) || !validateIATA(dest)) {
    showToast("Enter valid 3-letter airport codes", "error"); return;
  }
  if (!depDate) { showToast("Select a departure date", "error"); return; }

  alertBtn.disabled = true;
  alertBtn.innerHTML = `<span class="spinner"></span> Creating…`;

  try {
    await API.createAlert({ origin, destination: dest, departure_date: depDate,
      target_price: targetP, currency, email });
    showToast("Alert created!", "success");
    alertForm.reset();
    loadAlerts();
  } catch (err) {
    showToast("Error: " + err.message, "error");
  } finally {
    alertBtn.disabled = false;
    alertBtn.innerHTML = "🔔 Set Alert";
  }
});

// Load alerts when switching to that tab
navTabs.forEach(tab => {
  if (tab.dataset.section === "section-alerts") {
    tab.addEventListener("click", loadAlerts);
  }
});

// ── Init ─────────────────────────────────────────────────────────────────

// Set tomorrow as the minimum date for all date pickers using local timezone
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
const minDate = [
  tomorrow.getFullYear(),
  String(tomorrow.getMonth() + 1).padStart(2, "0"),
  String(tomorrow.getDate()).padStart(2, "0"),
].join("-");
document.querySelectorAll('input[type="date"]').forEach(inp => {
  inp.min = minDate;
});

showSection("section-search");
