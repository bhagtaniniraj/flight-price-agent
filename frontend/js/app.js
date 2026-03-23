/* ========== SkySearch SPA ========== */

// ---- Utility ----
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

function show(el) { if (el) el.style.display = ''; }
function hide(el) { if (el) el.style.display = 'none'; }
function showBlock(el) { if (el) el.style.display = 'block'; }
function showFlex(el) { if (el) el.style.display = 'flex'; }

function formatTime(dt) {
  const d = new Date(dt);
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
}

function formatDuration(mins) {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h > 0 ? `${h}h ${m > 0 ? m + 'm' : ''}`.trim() : `${m}m`;
}

function formatDate(dtStr) {
  const d = new Date(dtStr);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatPrice(p) {
  return '$' + p.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

// ---- Tab Navigation ----
const navBtns = $$('.nav-btn');
navBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    navBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.dataset.tab;
    $$('.tab-panel').forEach(p => p.classList.remove('active'));
    const panel = $(`#tab-${tab}`);
    if (panel) panel.classList.add('active');
    hide($('#hero'));
    if (tab === 'search') show($('#hero'));
  });
});

// ---- Date defaults ----
const departureDateInput = $('#departure-date');
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
departureDateInput.value = tomorrow.toISOString().split('T')[0];
departureDateInput.min = new Date().toISOString().split('T')[0];

const predDateInput = $('#pred-date');
const predDefault = new Date();
predDefault.setDate(predDefault.getDate() + 30);
predDateInput.value = predDefault.toISOString().split('T')[0];
predDateInput.min = new Date().toISOString().split('T')[0];

// ---- Autocomplete ----
let originSelected = null;
let destinationSelected = null;

function buildAutocomplete(inputId, dropdownId, onSelect) {
  const input = $(`#${inputId}`);
  const dropdown = $(`#${dropdownId}`);
  let debounce = null;
  let highlightIndex = -1;
  let currentItems = [];

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    const q = input.value.trim();
    if (q.length < 1) { dropdown.classList.remove('open'); return; }
    debounce = setTimeout(() => fetchSuggestions(q), 200);
  });

  input.addEventListener('keydown', (e) => {
    if (!dropdown.classList.contains('open')) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); highlightIndex = Math.min(highlightIndex + 1, currentItems.length - 1); renderHighlight(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); highlightIndex = Math.max(highlightIndex - 1, 0); renderHighlight(); }
    else if (e.key === 'Enter') { e.preventDefault(); if (highlightIndex >= 0 && currentItems[highlightIndex]) selectItem(currentItems[highlightIndex]); }
    else if (e.key === 'Escape') { dropdown.classList.remove('open'); }
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('open');
    }
  });

  async function fetchSuggestions(q) {
    try {
      const results = await api.searchAirports(q);
      currentItems = results;
      renderDropdown(results);
    } catch {}
  }

  function renderDropdown(items) {
    dropdown.innerHTML = '';
    highlightIndex = -1;
    if (!items.length) { dropdown.classList.remove('open'); return; }
    items.forEach((ap, i) => {
      const div = document.createElement('div');
      div.className = 'autocomplete-item';
      div.innerHTML = `
        <span class="autocomplete-code">${ap.iata_code}</span>
        <span class="autocomplete-sep">—</span>
        <span class="autocomplete-info">
          <span class="autocomplete-city">${ap.city}</span>
          <span class="autocomplete-name">(${ap.name})</span>
        </span>`;
      div.addEventListener('mouseenter', () => { highlightIndex = i; renderHighlight(); });
      div.addEventListener('click', () => selectItem(ap));
      dropdown.appendChild(div);
    });
    dropdown.classList.add('open');
  }

  function renderHighlight() {
    $$('.autocomplete-item', dropdown).forEach((el, i) => {
      el.classList.toggle('highlighted', i === highlightIndex);
    });
  }

  function selectItem(ap) {
    input.value = `${ap.city} (${ap.iata_code})`;
    dropdown.classList.remove('open');
    onSelect(ap);
  }

  return { clear() { input.value = ''; onSelect(null); } };
}

const originAC = buildAutocomplete('origin-input', 'origin-dropdown', (ap) => { originSelected = ap; });
const destAC = buildAutocomplete('destination-input', 'destination-dropdown', (ap) => { destinationSelected = ap; });

// Swap button
$('#swap-btn').addEventListener('click', () => {
  const tmpAP = originSelected;
  originSelected = destinationSelected;
  destinationSelected = tmpAP;
  const originInput = $('#origin-input');
  const destInput = $('#destination-input');
  const tmpVal = originInput.value;
  originInput.value = destInput.value;
  destInput.value = tmpVal;
});

// ---- Search ----
let lastSearchResults = [];
let lastSearchParams = {};

$('#search-btn').addEventListener('click', doSearch);

async function doSearch() {
  if (!originSelected) { alert('Please select an origin airport.'); return; }
  if (!destinationSelected) { alert('Please select a destination airport.'); return; }
  const depDate = departureDateInput.value;
  if (!depDate) { alert('Please select a departure date.'); return; }

  const passengers = parseInt($('#passengers').value);
  const seatClass = $('#seat-class').value;
  const sortBy = $('#sort-by').value;
  const stopsRadio = $$('input[name="stops"]').find(r => r.checked);
  const maxStops = stopsRadio && stopsRadio.value !== '' ? parseInt(stopsRadio.value) : null;
  const maxPriceInput = $('#max-price').value;
  const maxPrice = maxPriceInput ? parseFloat(maxPriceInput) : null;
  const selectedAirlines = $$('#airline-filters input:checked').map(cb => cb.value);

  lastSearchParams = { origin: originSelected.iata_code, destination: destinationSelected.iata_code, departureDate: depDate, passengers, seatClass, sortBy, maxStops, maxPrice, airlines: selectedAirlines };

  hide($('#results-area'));
  hide($('#search-empty'));
  hide($('#search-error'));
  show($('#search-loading'));

  try {
    const results = await api.searchFlights(lastSearchParams);
    lastSearchResults = results;
    hide($('#search-loading'));
    if (!results.length) { show($('#search-empty')); return; }
    renderResults(results, seatClass);
    buildAirlineFilters(results);
    show($('#results-area'));
  } catch (e) {
    hide($('#search-loading'));
    showBlock($('#search-error'));
    $('#search-error-msg').textContent = e.message;
  }
}

// Apply Filters button
$('#apply-filters-btn').addEventListener('click', doSearch);

function buildAirlineFilters(flights) {
  const airlineMap = {};
  flights.forEach(f => { if (!airlineMap[f.airline.iata_code]) airlineMap[f.airline.iata_code] = f.airline; });
  const container = $('#airline-filters');
  container.innerHTML = '';
  Object.values(airlineMap).forEach(al => {
    const label = document.createElement('label');
    label.className = 'airline-filter-item';
    label.innerHTML = `
      <input type="checkbox" value="${al.iata_code}" checked>
      <span class="airline-dot" style="background:${al.color}"></span>
      <span>${al.name}</span>`;
    container.appendChild(label);
  });
}

function renderResults(flights, seatClass) {
  const list = $('#flight-list');
  list.innerHTML = '';
  const count = $('#results-count');
  count.textContent = `${flights.length} flight${flights.length !== 1 ? 's' : ''} found`;

  const hasDeals = flights.some(f => f.is_deal);
  if (hasDeals) showBlock($('#deals-badge')); else hide($('#deals-badge'));

  flights.forEach((f, idx) => {
    const card = buildFlightCard(f, seatClass, idx === 0);
    list.appendChild(card);
  });
}

function buildFlightCard(f, seatClass, isBestPrice) {
  const card = document.createElement('div');
  card.className = `flight-card${f.is_deal ? ' is-deal' : ''}`;

  const depTime = formatTime(f.departure_time);
  const arrTime = formatTime(f.arrival_time);
  const dur = formatDuration(f.duration_minutes);
  const stopsLabel = f.stops === 0 ? 'Nonstop' : `${f.stops} stop${f.stops > 1 ? 's' : ''}`;
  const seatsClass = f.seats_available <= 5 ? 'seats-low' : 'seats-ok';
  const seatsText = f.seats_available <= 5 ? `⚠️ Only ${f.seats_available} seats left!` : `✓ ${f.seats_available} seats available`;
  const bagsText = f.bags_included === 0 ? 'No bags included' : `${f.bags_included} bag${f.bags_included > 1 ? 's' : ''} included`;
  const classLabel = seatClass.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());

  const isLive = f.source && f.source !== 'seed';
  const sourceBadge = isLive
    ? `<span class="badge-live">🟢 Live Price</span>`
    : `<span class="badge-sim">📊 Simulated</span>`;
  const bestBadge = isBestPrice ? `<span class="badge-best-price">🏆 Best Price</span>` : '';

  card.innerHTML = `
    <div class="flight-main">
      <div class="flight-header">
        <span class="airline-badge" style="background:${f.airline.color}">
          <span class="airline-badge-dot"></span>
          ${f.airline.name}
        </span>
        <span class="flight-number">${f.flight_number}</span>
        ${f.is_deal ? '<span class="deal-badge">🔥 DEAL</span>' : ''}
        ${sourceBadge}
        ${bestBadge}
      </div>
      <div class="flight-route">
        <div class="route-endpoint">
          <div class="route-time">${depTime}</div>
          <div class="route-code">${f.origin.iata_code}</div>
          <div class="route-city">${f.origin.city}</div>
        </div>
        <div class="route-middle">
          <div class="route-duration">${dur}</div>
          <div class="route-line">
            <span class="route-arrow">✈</span>
            <div class="route-line-inner"></div>
          </div>
          <div class="route-stops ${f.stops === 0 ? 'nonstop' : ''}">${stopsLabel}${f.layover_airports.length > 0 ? ' via ' + f.layover_airports.join(', ') : ''}</div>
        </div>
        <div class="route-endpoint">
          <div class="route-time">${arrTime}</div>
          <div class="route-code">${f.destination.iata_code}</div>
          <div class="route-city">${f.destination.city}</div>
        </div>
      </div>
      <div class="flight-meta">
        <span class="meta-item"><span class="meta-icon">🗓</span>${formatDate(f.departure_time)}</span>
        <span class="meta-item"><span class="meta-icon">🧳</span>${bagsText}</span>
        <span class="meta-item ${seatsClass}">${seatsText}</span>
      </div>
    </div>
    <div class="flight-right">
      <div>
        <div class="flight-price">${formatPrice(f.price)}</div>
        <div class="flight-price-label">per person · ${classLabel}</div>
      </div>
      ${f.booking_link
        ? `<a href="${f.booking_link}" target="_blank" rel="noopener" class="btn btn-primary book-btn">Book Now →</a>`
        : `<button class="btn btn-primary book-btn" data-flight-id="${f.id}">Book Now</button>`}
    </div>`;

  const bookBtn = card.querySelector('.book-btn');
  if (bookBtn && !f.booking_link) {
    bookBtn.addEventListener('click', () => openBookingModal(f, seatClass));
  }
  return card;
}

// ---- Booking Modal ----
let currentBookingFlight = null;
let currentBookingSeatClass = null;

function openBookingModal(flight, seatClass) {
  currentBookingFlight = flight;
  currentBookingSeatClass = seatClass;

  const summary = $('#modal-flight-summary');
  summary.innerHTML = `
    <strong>${flight.origin.city} (${flight.origin.iata_code}) → ${flight.destination.city} (${flight.destination.iata_code})</strong><br>
    ${flight.airline.name} · ${flight.flight_number} · ${formatDate(flight.departure_time)}<br>
    Departure: <strong>${formatTime(flight.departure_time)}</strong> — Arrival: <strong>${formatTime(flight.arrival_time)}</strong><br>
    Duration: ${formatDuration(flight.duration_minutes)} · ${flight.stops === 0 ? 'Nonstop' : flight.stops + ' stop(s)'}`;

  updateModalPrice();

  hide($('#booking-error'));
  hide($('#booking-success'));
  show($('#modal-footer'));
  show($('#booking-modal'));
}

function updateModalPrice() {
  const count = parseInt($('#booking-passengers').value) || 1;
  const total = currentBookingFlight ? currentBookingFlight.price * count : 0;
  $('#modal-total-price').textContent = formatPrice(total);
}

$('#booking-passengers').addEventListener('change', updateModalPrice);

$('#modal-close').addEventListener('click', closeModal);
$('#modal-cancel').addEventListener('click', closeModal);
$('#booking-modal').addEventListener('click', (e) => { if (e.target === $('#booking-modal')) closeModal(); });

function closeModal() {
  hide($('#booking-modal'));
  $('#booking-name').value = '';
  $('#booking-email').value = '';
  $('#booking-passengers').value = '1';
  currentBookingFlight = null;
}

$('#confirm-booking-btn').addEventListener('click', async () => {
  const name = $('#booking-name').value.trim();
  const email = $('#booking-email').value.trim();
  const count = parseInt($('#booking-passengers').value);

  if (!name) { showError($('#booking-error'), 'Please enter your full name.'); return; }
  if (!email || !email.includes('@')) { showError($('#booking-error'), 'Please enter a valid email.'); return; }

  hide($('#booking-error'));
  const btn = $('#confirm-booking-btn');
  btn.disabled = true;
  btn.textContent = 'Processing...';

  try {
    const booking = await api.createBooking({
      flightId: currentBookingFlight.id,
      passengerName: name,
      passengerEmail: email,
      passengerCount: count,
      seatClass: currentBookingSeatClass,
    });

    hide($('#modal-footer'));
    $('#booking-ref').textContent = booking.booking_reference;
    $('#booking-email-confirm').textContent = email;

    // Show Pay Now button
    const payBtn = $('#pay-now-btn');
    if (payBtn) {
      payBtn.style.display = '';
      payBtn.onclick = async () => {
        payBtn.disabled = true;
        payBtn.textContent = 'Redirecting to payment...';
        try {
          const origin = window.location.origin;
          const session = await api.createCheckoutSession(
            booking.id,
            `${origin}/?payment=success&ref=${booking.booking_reference}`,
            `${origin}/?payment=cancel&ref=${booking.booking_reference}`,
          );
          window.location.href = session.checkout_url;
        } catch (err) {
          payBtn.disabled = false;
          payBtn.textContent = 'Pay Now';
          showError($('#booking-error'), err.message);
        }
      };
    }

    show($('#booking-success'));
  } catch (e) {
    showError($('#booking-error'), e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Confirm Booking';
  }
});

function showError(el, msg) {
  el.textContent = msg;
  show(el);
}

// ---- My Bookings ----
$('#bookings-lookup-btn').addEventListener('click', async () => {
  const email = $('#bookings-email').value.trim();
  if (!email) { alert('Please enter your email address.'); return; }
  loadBookings(email);
});

$('#bookings-email').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') $('#bookings-lookup-btn').click();
});

async function loadBookings(email) {
  const list = $('#bookings-list');
  list.innerHTML = '';
  hide($('#bookings-empty'));
  show($('#bookings-loading'));

  try {
    const bookings = await api.getBookings(email);
    hide($('#bookings-loading'));
    if (!bookings.length) { show($('#bookings-empty')); return; }
    bookings.forEach(b => list.appendChild(buildBookingCard(b)));
  } catch (e) {
    hide($('#bookings-loading'));
    list.innerHTML = `<p style="color:var(--danger);padding:1rem;">${e.message}</p>`;
  }
}

function buildBookingCard(b) {
  const card = document.createElement('div');
  card.className = 'booking-card';
  card.innerHTML = `
    <div>
      <div class="booking-ref">Booking Reference: <span>${b.booking_reference}</span></div>
      <div class="booking-route">${b.flight.origin.city} (${b.flight.origin.iata_code}) → ${b.flight.destination.city} (${b.flight.destination.iata_code})</div>
      <div class="booking-detail">${b.flight.airline.name} · ${b.flight.flight_number} · ${formatDate(b.flight.departure_time)} · ${formatTime(b.flight.departure_time)}</div>
      <div class="booking-detail">${b.passenger_count} passenger${b.passenger_count > 1 ? 's' : ''} · ${b.seat_class.replace('_', ' ')}</div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.5rem;">
      <span class="booking-status ${b.status}">${b.status}</span>
      <span class="booking-price">${formatPrice(b.total_price)}</span>
      ${b.status === 'confirmed' ? `<button class="btn btn-danger cancel-btn" data-id="${b.id}">Cancel</button>` : ''}
    </div>`;

  const cancelBtn = card.querySelector('.cancel-btn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', async () => {
      if (!confirm('Cancel this booking?')) return;
      try {
        await api.cancelBooking(b.id);
        loadBookings($('#bookings-email').value.trim());
      } catch (e) {
        alert(e.message);
      }
    });
  }
  return card;
}

// ---- Price Alerts ----
$('#create-alert-btn').addEventListener('click', async () => {
  const origin = $('#alert-origin').value.trim().toUpperCase();
  const dest = $('#alert-destination').value.trim().toUpperCase();
  const price = parseFloat($('#alert-price').value);
  const email = $('#alert-email').value.trim();

  hide($('#alert-success'));
  hide($('#alert-error'));

  if (!origin || origin.length !== 3) { showError($('#alert-error'), 'Enter a valid 3-letter origin code.'); return; }
  if (!dest || dest.length !== 3) { showError($('#alert-error'), 'Enter a valid 3-letter destination code.'); return; }
  if (!price || price <= 0) { showError($('#alert-error'), 'Enter a valid target price.'); return; }
  if (!email || !email.includes('@')) { showError($('#alert-error'), 'Enter a valid email address.'); return; }

  try {
    await api.createAlert({ originIata: origin, destinationIata: dest, targetPrice: price, userEmail: email });
    $('#alert-success').textContent = `✅ Alert created! We'll notify ${email} when ${origin} → ${dest} drops below ${formatPrice(price)}.`;
    show($('#alert-success'));
    $('#alert-origin').value = '';
    $('#alert-destination').value = '';
    $('#alert-price').value = '';

    // Auto-load this email's alerts
    $('#alerts-lookup-email').value = email;
    loadAlerts(email);
  } catch (e) {
    showError($('#alert-error'), e.message);
  }
});

$('#alerts-lookup-btn').addEventListener('click', () => {
  const email = $('#alerts-lookup-email').value.trim();
  if (!email) { alert('Please enter an email.'); return; }
  loadAlerts(email);
});

async function loadAlerts(email) {
  const list = $('#alerts-list');
  list.innerHTML = '';
  hide($('#alerts-empty'));
  show($('#alerts-loading'));

  try {
    const alerts = await api.getAlerts(email);
    hide($('#alerts-loading'));
    if (!alerts.length) { show($('#alerts-empty')); return; }
    alerts.forEach(a => list.appendChild(buildAlertCard(a, email)));
  } catch (e) {
    hide($('#alerts-loading'));
    list.innerHTML = `<p style="color:var(--danger);padding:1rem;">${e.message}</p>`;
  }
}

function buildAlertCard(a, email) {
  const card = document.createElement('div');
  card.className = 'alert-card';
  card.innerHTML = `
    <div>
      <div class="alert-route">${a.origin_iata} → ${a.destination_iata}</div>
      <div class="alert-target">Alert when price drops below <strong>${formatPrice(a.target_price)}</strong></div>
    </div>
    <button class="btn btn-danger" data-id="${a.id}">Delete</button>`;

  card.querySelector('.btn-danger').addEventListener('click', async () => {
    try {
      await api.deleteAlert(a.id);
      loadAlerts(email);
    } catch (e) {
      alert(e.message);
    }
  });
  return card;
}

// ---- Price Predictions ----
$('#pred-btn').addEventListener('click', async () => {
  const origin = $('#pred-origin').value.trim().toUpperCase();
  const dest = $('#pred-destination').value.trim().toUpperCase();
  const travelDate = $('#pred-date').value;

  if (!origin || origin.length !== 3) { alert('Enter a valid 3-letter origin code.'); return; }
  if (!dest || dest.length !== 3) { alert('Enter a valid 3-letter destination code.'); return; }
  if (!travelDate) { alert('Select a travel date.'); return; }

  hide($('#pred-result'));
  hide($('#pred-error'));
  show($('#pred-loading'));

  try {
    const data = await api.getPrediction(origin, dest, travelDate);
    hide($('#pred-loading'));
    renderPrediction(data);
    show($('#pred-result'));
  } catch (e) {
    hide($('#pred-loading'));
    if (e.message === 'NOT_FOUND') {
      show($('#pred-error'));
    } else {
      $('#pred-error').querySelector('p').textContent = e.message;
      show($('#pred-error'));
    }
  }
});

function renderPrediction(data) {
  $('#pred-route-label').textContent = `${data.origin} → ${data.destination} · ${data.travel_date}`;
  $('#pred-current-price').textContent = formatPrice(data.current_avg_price);
  $('#pred-predicted-price').textContent = formatPrice(data.predicted_price);

  const arrowEl = $('#pred-arrow');
  if (data.trend === 'rising') { arrowEl.textContent = '↗'; arrowEl.style.color = '#fca5a5'; }
  else if (data.trend === 'falling') { arrowEl.textContent = '↘'; arrowEl.style.color = '#6ee7b7'; }
  else { arrowEl.textContent = '→'; arrowEl.style.color = 'rgba(255,255,255,0.6)'; }

  const trendBadge = $('#pred-trend-badge');
  trendBadge.textContent = `📈 ${data.trend.toUpperCase()}`;
  trendBadge.className = `pred-trend-badge ${data.trend}`;
  if (data.trend === 'falling') trendBadge.textContent = `📉 ${data.trend.toUpperCase()}`;
  else if (data.trend === 'stable') trendBadge.textContent = `📊 ${data.trend.toUpperCase()}`;

  $('#pred-confidence').textContent = `Confidence: ${Math.round(data.confidence * 100)}%`;

  const recEl = $('#pred-recommendation');
  if (data.recommendation === 'buy_now') {
    recEl.className = 'pred-recommendation buy-now';
    recEl.textContent = '🛒 Recommendation: Buy Now — prices are likely to rise!';
  } else {
    recEl.className = 'pred-recommendation wait';
    recEl.textContent = '⏳ Recommendation: Wait — prices may drop further.';
  }

  renderPriceChart(data.price_history);
}

function renderPriceChart(history) {
  const chart = $('#price-chart');
  const labelsEl = $('#chart-labels');
  chart.innerHTML = '';
  labelsEl.innerHTML = '';

  const prices = history.map(p => p.price);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const range = maxP - minP || 1;

  history.forEach((point, i) => {
    const heightPct = ((point.price - minP) / range) * 80 + 10;

    const wrap = document.createElement('div');
    wrap.className = 'chart-bar-wrap';

    const bar = document.createElement('div');
    bar.className = 'chart-bar';
    bar.style.height = `${heightPct}%`;

    const tooltip = document.createElement('div');
    tooltip.className = 'chart-bar-tooltip';
    tooltip.textContent = formatPrice(point.price);
    bar.appendChild(tooltip);

    wrap.appendChild(bar);
    chart.appendChild(wrap);

    const label = document.createElement('div');
    label.className = 'chart-label-item';
    // Show date abbreviated
    const d = new Date(point.date);
    label.textContent = (i % 3 === 0) ? `${d.getMonth()+1}/${d.getDate()}` : '';
    labelsEl.appendChild(label);
  });
}
