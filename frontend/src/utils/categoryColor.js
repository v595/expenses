const PALETTE = [
  "#4f46e5", "#0891b2", "#d97706", "#db2777",
  "#65a30d", "#7c3aed", "#0d9488", "#ea580c",
];

// Deterministic color per category name, so "Food" always gets the same
// dot/badge color everywhere without having to maintain a fixed category list.
export function categoryColor(category) {
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = category.charCodeAt(i) + ((hash << 5) - hash);
  }
  return PALETTE[Math.abs(hash) % PALETTE.length];
}
