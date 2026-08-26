// Parses the same shape downloadTransactionsCsv exports: a header row of
// Date,Type,Category,Description,Amount, then one row per transaction.
// Handles quoted fields (commas/quotes inside a value) the same way that
// exporter escapes them.
function parseCsvLine(line) {
  const fields = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (inQuotes) {
      if (char === '"' && line[i + 1] === '"') {
        current += '"';
        i++;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        current += char;
      }
    } else if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      fields.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  fields.push(current);
  return fields;
}

export function parseTransactionsCsv(text) {
  const lines = text.split(/\r?\n/).filter((line) => line.trim() !== "");
  if (lines.length < 2) return [];

  const header = parseCsvLine(lines[0]).map((h) => h.trim().toLowerCase());
  const dateIdx = header.indexOf("date");
  const typeIdx = header.indexOf("type");
  const categoryIdx = header.indexOf("category");
  const descriptionIdx = header.indexOf("description");
  const amountIdx = header.indexOf("amount");

  return lines.slice(1).map((line) => {
    const fields = parseCsvLine(line);
    return {
      date: fields[dateIdx]?.trim(),
      type: fields[typeIdx]?.trim().toLowerCase(),
      category: fields[categoryIdx]?.trim(),
      description: fields[descriptionIdx]?.trim() || "",
      amount: Number(fields[amountIdx]),
    };
  });
}
