import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

const BRAND = [79, 70, 229]; // matches --color-primary
const BRAND_END = [124, 58, 237]; // violet — gradient endpoint for header/accents
const INCOME = [22, 163, 74];
const INCOME_END = [5, 150, 105];
const EXPENSE = [220, 38, 38];
const EXPENSE_END = [190, 24, 93];
const MUTED = [107, 114, 128];
const INK = [17, 24, 39];

// jsPDF has no native gradient fill, so a horizontal gradient is faked with
// thin interpolated vertical strips — the standard PDF trick for this.
function drawGradientRect(doc, x, y, w, h, colorStart, colorEnd) {
  const steps = Math.max(20, Math.round(w));
  const stepWidth = w / steps;
  for (let i = 0; i < steps; i++) {
    const t = i / (steps - 1);
    const r = colorStart[0] + (colorEnd[0] - colorStart[0]) * t;
    const g = colorStart[1] + (colorEnd[1] - colorStart[1]) * t;
    const b = colorStart[2] + (colorEnd[2] - colorStart[2]) * t;
    doc.setFillColor(r, g, b);
    doc.rect(x + i * stepWidth, y, stepWidth + 0.5, h, "F");
  }
}

function formatMoney(amount) {
  return `Rs. ${Number(amount).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// "week" = last 7 days, "month" = current calendar month, "year" = current calendar year.
export function getRangeForPeriod(period) {
  const end = new Date();
  const start = new Date();

  if (period === "week") {
    start.setDate(end.getDate() - 6);
  } else if (period === "month") {
    start.setDate(1);
  } else if (period === "year") {
    start.setMonth(0, 1);
  }

  const toISO = (d) => d.toISOString().slice(0, 10);
  return { start_date: toISO(start), end_date: toISO(end) };
}

const PERIOD_LABEL = { week: "Weekly", month: "Monthly", year: "Yearly" };

function statBlock(doc, x, y, width, label, value, colorStart, colorEnd) {
  doc.setFillColor(248, 248, 251);
  doc.roundedRect(x, y, width, 22, 3, 3, "F");
  // Gradient accent bar down the left edge of the card.
  drawGradientRect(doc, x, y, 2.2, 22, colorStart, colorEnd);
  doc.setFontSize(8.5);
  doc.setTextColor(...MUTED);
  doc.text(label.toUpperCase(), x + 6, y + 8);
  doc.setFontSize(13);
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colorStart);
  doc.text(value, x + 6, y + 17);
  doc.setFont(undefined, "normal");
}

export function downloadReportPdf({ period, userName, transactions, range }) {
  const income = transactions.filter((t) => t.type === "income").reduce((s, t) => s + t.amount, 0);
  const expenses = transactions.filter((t) => t.type === "expense").reduce((s, t) => s + t.amount, 0);
  const balance = income - expenses;

  const categoryTotals = {};
  transactions
    .filter((t) => t.type === "expense")
    .forEach((t) => {
      categoryTotals[t.category] = (categoryTotals[t.category] || 0) + t.amount;
    });
  const topCategories = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1]);

  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();

  // --- Header band ---
  drawGradientRect(doc, 0, 0, pageWidth, 34, BRAND, BRAND_END);
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(17);
  doc.setFont(undefined, "bold");
  doc.text("Expense Tracker", 14, 15);
  doc.setFontSize(10.5);
  doc.setFont(undefined, "normal");
  doc.text(`${PERIOD_LABEL[period]} Budget Report`, 14, 23);
  doc.setFontSize(8.5);
  doc.setTextColor(220, 220, 255);
  doc.text(`${userName}  |  ${range.start_date} to ${range.end_date}`, 14, 29.5);

  // --- Stat cards ---
  const cardY = 42;
  const gap = 6;
  const cardWidth = (pageWidth - 28 - gap * 2) / 3;
  statBlock(doc, 14, cardY, cardWidth, "Total Income", formatMoney(income), INCOME, INCOME_END);
  statBlock(
    doc,
    14 + cardWidth + gap,
    cardY,
    cardWidth,
    "Total Expenses",
    formatMoney(expenses),
    EXPENSE,
    EXPENSE_END
  );
  statBlock(
    doc,
    14 + (cardWidth + gap) * 2,
    cardY,
    cardWidth,
    "Net Balance",
    formatMoney(balance),
    ...(balance >= 0 ? [INCOME, INCOME_END] : [EXPENSE, EXPENSE_END])
  );

  let cursorY = cardY + 30;

  // --- Category breakdown ---
  if (topCategories.length > 0) {
    drawGradientRect(doc, 14, cursorY - 3.2, 3, 3, BRAND, BRAND_END);
    doc.setFontSize(11);
    doc.setTextColor(...INK);
    doc.setFont(undefined, "bold");
    doc.text("Top Spending Categories", 19, cursorY);
    doc.setFont(undefined, "normal");

    autoTable(doc, {
      startY: cursorY + 4,
      head: [["Category", "Amount", "% of Expenses"]],
      body: topCategories.map(([category, total]) => [
        category,
        formatMoney(total),
        expenses > 0 ? `${((total / expenses) * 100).toFixed(1)}%` : "0%",
      ]),
      styles: { fontSize: 9, cellPadding: 3 },
      headStyles: { fillColor: BRAND, textColor: 255 },
      alternateRowStyles: { fillColor: [248, 248, 251] },
      margin: { left: 14, right: 14 },
    });

    cursorY = doc.lastAutoTable.finalY + 10;
  }

  // --- Transaction detail ---
  drawGradientRect(doc, 14, cursorY - 3.2, 3, 3, BRAND, BRAND_END);
  doc.setFontSize(11);
  doc.setTextColor(...INK);
  doc.setFont(undefined, "bold");
  doc.text("Transaction Detail", 19, cursorY);
  doc.setFont(undefined, "normal");

  autoTable(doc, {
    startY: cursorY + 4,
    head: [["Date", "Type", "Category", "Description", "Amount"]],
    body: transactions
      .slice()
      .sort((a, b) => (a.date < b.date ? 1 : -1))
      .map((t) => [
        t.date,
        t.type === "income" ? "Income" : "Expense",
        t.category,
        t.description || "-",
        formatMoney(t.amount),
      ]),
    styles: { fontSize: 8.5, cellPadding: 3 },
    headStyles: { fillColor: BRAND, textColor: 255 },
    alternateRowStyles: { fillColor: [248, 248, 251] },
    columnStyles: { 4: { halign: "right" } },
    margin: { left: 14, right: 14 },
    didParseCell: (data) => {
      if (data.section === "body" && data.column.index === 1) {
        data.cell.styles.textColor = data.cell.raw === "Income" ? INCOME : EXPENSE;
        data.cell.styles.fontStyle = "bold";
      }
    },
    didDrawPage: () => {
      const pageCount = doc.internal.getNumberOfPages();
      const pageHeight = doc.internal.pageSize.getHeight();
      doc.setFontSize(8);
      doc.setTextColor(...MUTED);
      doc.text(
        `Generated ${new Date().toLocaleDateString()} - Expense Tracker`,
        14,
        pageHeight - 8
      );
      doc.text(`Page ${pageCount}`, pageWidth - 20, pageHeight - 8);
    },
  });

  if (transactions.length === 0) {
    doc.setFontSize(9.5);
    doc.setTextColor(...MUTED);
    doc.text("No transactions recorded in this period.", 14, cursorY + 10);
  }

  doc.save(`${period}-budget-report.pdf`);
}
