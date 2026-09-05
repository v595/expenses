// Currency conversion for display.
//
// Design rule: stored amounts are NEVER rewritten. Every amount in the
// database is held in BASE_CURRENCY, and switching the display currency only
// changes how it is rendered. Converting the stored rows instead would be
// wrong twice over — a ₹500 lunch was ₹500 on the day it happened, and
// re-converting on every switch would round-trip the numbers away (₹500 → $6
// → ₹498…). So rates are applied at the last moment, on screen.

export const BASE_CURRENCY = "INR";

// Fallback used when the network is unavailable. Deliberately rough — it
// exists so the app degrades to "approximately right" rather than showing
// rupee amounts labelled with a dollar sign, which is the bug this fixes.
const FALLBACK_RATES = {
  INR: 1,
  USD: 0.012,
  EUR: 0.011,
  GBP: 0.0094,
  JPY: 1.78,
  AUD: 0.018,
  CAD: 0.016,
};

const CACHE_KEY = "fx-rates-v1";
const MAX_AGE_MS = 12 * 60 * 60 * 1000; // 12h — FX moves slower than this app needs.

let rates = { ...FALLBACK_RATES };
let isLive = false;

function readCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.rates || Date.now() - parsed.at > MAX_AGE_MS) return null;
    return parsed;
  } catch {
    // Private mode / cleared storage / corrupt JSON — just refetch.
    return null;
  }
}

const cached = readCache();
if (cached) {
  rates = { ...FALLBACK_RATES, ...cached.rates };
  isLive = true;
}

/** Fetches fresh rates once per session (and at most twice a day). */
export async function loadRates() {
  if (readCache()) return rates;
  try {
    const res = await fetch(`https://open.er-api.com/v6/latest/${BASE_CURRENCY}`);
    if (!res.ok) throw new Error("rate fetch failed");
    const data = await res.json();
    if (!data?.rates) throw new Error("unexpected rate payload");
    rates = { ...FALLBACK_RATES, ...data.rates };
    isLive = true;
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), rates: data.rates }));
    } catch {
      // Not being able to cache is not a reason to fail the conversion.
    }
  } catch {
    // Offline or the endpoint is down: keep the fallback table. Amounts stay
    // approximately correct and `ratesAreLive()` reports the difference.
    isLive = false;
  }
  return rates;
}

export function ratesAreLive() {
  return isLive;
}

/** Converts an amount held in BASE_CURRENCY into `currency`. */
export function fromBase(amount, currency) {
  const value = Number(amount);
  if (!Number.isFinite(value)) return 0;
  if (!currency || currency === BASE_CURRENCY) return value;
  return value * (rates[currency] ?? 1);
}

/** Converts an amount typed in `currency` back into BASE_CURRENCY for storage. */
export function toBase(amount, currency) {
  const value = Number(amount);
  if (!Number.isFinite(value)) return 0;
  if (!currency || currency === BASE_CURRENCY) return value;
  const rate = rates[currency];
  if (!rate) return value;
  return value / rate;
}
