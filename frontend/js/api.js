/* global API client */
const api = {
  async searchFlights({ origin, destination, departureDate, passengers = 1, seatClass = 'economy', sortBy = 'price', maxStops, maxPrice, airlines }) {
    const params = new URLSearchParams({
      origin,
      destination,
      departure_date: departureDate,
      passengers,
      seat_class: seatClass,
      sort_by: sortBy,
    });
    if (maxStops !== undefined && maxStops !== null && maxStops !== '') params.set('max_stops', maxStops);
    if (maxPrice !== undefined && maxPrice !== null && maxPrice !== '') params.set('max_price', maxPrice);
    if (airlines && airlines.length > 0) params.set('airlines', airlines.join(','));
    const res = await fetch(`/api/flights/search?${params}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Search failed (${res.status})`);
    }
    return res.json();
  },

  async searchAirports(q) {
    const params = new URLSearchParams({ q });
    const res = await fetch(`/api/airports?${params}`);
    if (!res.ok) throw new Error('Airport lookup failed');
    return res.json();
  },

  async getAirport(code) {
    const res = await fetch(`/api/airports/${code}`);
    if (!res.ok) return null;
    return res.json();
  },

  async createBooking({ flightId, passengerName, passengerEmail, passengerCount, seatClass }) {
    const res = await fetch('/api/bookings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        flight_id: flightId,
        passenger_name: passengerName,
        passenger_email: passengerEmail,
        passenger_count: passengerCount,
        seat_class: seatClass,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Booking failed (${res.status})`);
    }
    return res.json();
  },

  async getBookings(email) {
    const res = await fetch(`/api/bookings?email=${encodeURIComponent(email)}`);
    if (!res.ok) throw new Error('Could not load bookings');
    return res.json();
  },

  async cancelBooking(id) {
    const res = await fetch(`/api/bookings/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Could not cancel booking');
  },

  async createAlert({ originIata, destinationIata, targetPrice, userEmail }) {
    const res = await fetch('/api/alerts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        origin_iata: originIata,
        destination_iata: destinationIata,
        target_price: targetPrice,
        user_email: userEmail,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Alert creation failed (${res.status})`);
    }
    return res.json();
  },

  async getAlerts(email) {
    const res = await fetch(`/api/alerts?email=${encodeURIComponent(email)}`);
    if (!res.ok) throw new Error('Could not load alerts');
    return res.json();
  },

  async deleteAlert(id) {
    const res = await fetch(`/api/alerts/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Could not delete alert');
  },

  async getPrediction(origin, destination, travelDate) {
    const params = new URLSearchParams({ origin, destination, travel_date: travelDate });
    const res = await fetch(`/api/predictions?${params}`);
    if (!res.ok) {
      if (res.status === 404) throw new Error('NOT_FOUND');
      throw new Error('Prediction failed');
    }
    return res.json();
  },

  async createCheckoutSession(bookingId, successUrl, cancelUrl) {
    const res = await fetch('/api/payments/create-checkout-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        booking_id: bookingId,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Payment session creation failed (${res.status})`);
    }
    return res.json();
  },

  async getPaymentStatus(bookingId) {
    const res = await fetch(`/api/payments/status/${bookingId}`);
    if (!res.ok) throw new Error('Could not get payment status');
    return res.json();
  },
};
