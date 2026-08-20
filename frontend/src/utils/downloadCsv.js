function escapeCsvField(value) {
  const str = String(value ?? "");
  return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
}

export function downloadTransactionsCsv(transactions) {
  const header = ["Date", "Type", "Category", "Description", "Amount"];
  const rows = transactions.map((t) => [t.date, t.type, t.category, t.description || "", t.amount]);
  const csv = [header, ...rows].map((row) => row.map(escapeCsvField).join(",")).join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "transactions.csv";
  link.click();
  URL.revokeObjectURL(url);
}
