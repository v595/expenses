function escapeCsvField(value) {
  const str = String(value ?? "");
  return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
}

function downloadCsvFile(rows, fileName) {
  const csv = rows.map((row) => row.map(escapeCsvField).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

export function downloadTransactionsCsv(transactions) {
  const header = ["Date", "Type", "Category", "Description", "Amount"];
  const rows = transactions.map((t) => [t.date, t.type, t.category, t.description || "", t.amount]);
  downloadCsvFile([header, ...rows], "transactions.csv");
}

// One row per category+type, totalled — the shape a tax filer or accountant
// actually wants, rather than every individual transaction.
export function downloadCategorySummaryCsv(transactions, fileName) {
  const totals = {};
  transactions.forEach((t) => {
    const key = `${t.type}::${t.category}`;
    totals[key] = (totals[key] || 0) + t.amount;
  });

  const header = ["Type", "Category", "Total"];
  const rows = Object.entries(totals)
    .map(([key, total]) => {
      const [type, category] = key.split("::");
      return [type === "income" ? "Income" : "Expense", category, total.toFixed(2)];
    })
    .sort((a, b) => (a[0] === b[0] ? b[2] - a[2] : a[0].localeCompare(b[0])));

  const totalIncome = transactions.filter((t) => t.type === "income").reduce((s, t) => s + t.amount, 0);
  const totalExpense = transactions.filter((t) => t.type === "expense").reduce((s, t) => s + t.amount, 0);
  rows.push([], ["Total Income", "", totalIncome.toFixed(2)], ["Total Expense", "", totalExpense.toFixed(2)]);

  downloadCsvFile([header, ...rows], fileName || "category-summary.csv");
}
