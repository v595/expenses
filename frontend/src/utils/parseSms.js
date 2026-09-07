// Best-effort parser for common Indian bank transaction SMS text, pasted by
// hand (there's no way for a web app to read a phone's SMS inbox directly —
// this is the manual alternative). Never auto-saves anything: the result is
// only ever used to pre-fill the transaction form for the user to review.

const AMOUNT_PATTERN = /(?:Rs\.?|INR|₹)\s?([\d,]+(?:\.\d{1,2})?)/i;
const DATE_PATTERN = /\bon\s+(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b/i;
const DEBIT_WORDS = /\b(debited|spent|paid|withdrawn|purchase of)\b/i;
const CREDIT_WORDS = /\b(credited|received|deposited)\b/i;

// Merchant/description hints, roughly in the order banks tend to phrase them.
const DESCRIPTION_PATTERNS = [
  /\bto\s+(?:VPA\s+)?([A-Za-z0-9@._\-\s]+?)(?:\s+on\b|\s+Avl\b|\.|$)/i,
  /\bat\s+([A-Za-z0-9@._\-\s]+?)(?:\s+on\b|\s+Avl\b|\.|$)/i,
  /\bfrom\s+([A-Za-z0-9@._\-\s]+?)(?:\s+on\b|\s+Avl\b|\.|$)/i,
];

function toIsoDate(day, month, year) {
  const y = year.length === 2 ? `20${year}` : year;
  const d = day.padStart(2, "0");
  const m = month.padStart(2, "0");
  return `${y}-${m}-${d}`;
}

// Returns { amount, type, date, description } with whichever fields could be
// confidently extracted (missing ones are left out — the caller fills in
// sensible defaults, e.g. today's date). Returns null if it couldn't even
// find an amount, since nothing useful can be pre-filled without one.
export function parseSmsText(text) {
  if (!text || typeof text !== "string") return null;

  const amountMatch = text.match(AMOUNT_PATTERN);
  if (!amountMatch) return null;
  const amount = Number(amountMatch[1].replace(/,/g, ""));
  if (!amount || Number.isNaN(amount)) return null;

  const result = { amount };

  if (DEBIT_WORDS.test(text)) result.type = "expense";
  else if (CREDIT_WORDS.test(text)) result.type = "income";

  const dateMatch = text.match(DATE_PATTERN);
  if (dateMatch) {
    const [, day, month, year] = dateMatch;
    result.date = toIsoDate(day, month, year);
  }

  for (const pattern of DESCRIPTION_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      const description = match[1].trim().replace(/\s{2,}/g, " ");
      if (description.length > 0 && description.length <= 60) {
        result.description = description;
        break;
      }
    }
  }

  return result;
}
