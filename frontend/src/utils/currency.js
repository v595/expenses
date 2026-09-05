// Currency support. Amounts are stored in one base currency (see utils/fx.js)
// and converted at render time, so switching currency changes the numbers as
// well as the symbol — it used to only relabel them, which made ₹1,450 read
// as "$1,450".
import { fromBase } from "./fx";

export const CURRENCIES = [
  { code: "USD", symbol: "$", label: "US Dollar" },
  { code: "EUR", symbol: "€", label: "Euro" },
  { code: "GBP", symbol: "£", label: "British Pound" },
  { code: "INR", symbol: "₹", label: "Indian Rupee" },
  { code: "JPY", symbol: "¥", label: "Japanese Yen" },
  { code: "AUD", symbol: "A$", label: "Australian Dollar" },
  { code: "CAD", symbol: "C$", label: "Canadian Dollar" },
];

// The app is rupee-first: anything without an explicit currency falls back to
// INR rather than USD, so a missing/legacy value never renders as dollars.
export const DEFAULT_CURRENCY = "INR";

export function currencySymbol(code) {
  return CURRENCIES.find((c) => c.code === code)?.symbol || "₹";
}

export function formatMoney(amount, currencyCode = DEFAULT_CURRENCY) {
  // Stored amounts are in the base currency; convert before rendering.
  const value = fromBase(amount, currencyCode);
  if (!Number.isFinite(value)) return `${currencySymbol(currencyCode)}0.00`;

  // Rupees group the Indian way (1,00,000 rather than 100,000), so INR uses
  // the en-IN locale; everything else keeps standard thousands grouping.
  const locale = currencyCode === "INR" ? "en-IN" : "en-US";
  const formatted = value.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${currencySymbol(currencyCode)}${formatted}`;
}
