// Client-side receipt OCR via Tesseract.js — dynamically imported so its
// (fairly large) wasm/worker bundle only loads when a receipt is actually
// scanned, not on every page load.

// "Total"/"Amount" lines take priority since a receipt usually also prints
// subtotal, tax, and item prices — the number right after one of these
// keywords is the actual amount paid, not just the largest number on the page.
const LABELLED_AMOUNT_PATTERN = /(?:total|amount|grand total|net total|amount due|paid)\D{0,10}?(\d[\d,]*\.\d{2})/i;
const ANY_AMOUNT_PATTERN = /(\d[\d,]*\.\d{2})/g;

function bestGuessAmount(text) {
  const labelled = text.match(LABELLED_AMOUNT_PATTERN);
  if (labelled) return Number(labelled[1].replace(/,/g, ""));

  const all = [...text.matchAll(ANY_AMOUNT_PATTERN)].map((m) => Number(m[1].replace(/,/g, "")));
  if (all.length === 0) return null;
  // Fall back to the largest figure on the receipt — usually the total, since
  // it's the sum of everything else printed.
  return Math.max(...all);
}

// dataUrl: a "data:image/..." string (what the receipt file input already
// produces). Returns { amount, text } — amount is null if nothing looked
// like a price. Never throws; OCR failing just means no pre-fill happens.
export async function scanReceiptForAmount(dataUrl) {
  try {
    const { recognize } = await import("tesseract.js");
    const {
      data: { text },
    } = await recognize(dataUrl, "eng");
    return { amount: bestGuessAmount(text), text };
  } catch {
    return { amount: null, text: "" };
  }
}
