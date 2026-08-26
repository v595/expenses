// Display-only currency support: we store a 3-letter code on the user and
// show the right symbol everywhere. No live FX conversion — amounts are
// entered and stored as-is, just relabeled.
export const CURRENCIES = [
  { code: "USD", symbol: "$", label: "US Dollar" },
  { code: "EUR", symbol: "€", label: "Euro" },
  { code: "GBP", symbol: "£", label: "British Pound" },
  { code: "INR", symbol: "₹", label: "Indian Rupee" },
  { code: "JPY", symbol: "¥", label: "Japanese Yen" },
  { code: "AUD", symbol: "A$", label: "Australian Dollar" },
  { code: "CAD", symbol: "C$", label: "Canadian Dollar" },
];

export function currencySymbol(code) {
  return CURRENCIES.find((c) => c.code === code)?.symbol || "$";
}

export function formatMoney(amount, currencyCode = "USD") {
  return `${currencySymbol(currencyCode)}${Number(amount).toFixed(2)}`;
}
