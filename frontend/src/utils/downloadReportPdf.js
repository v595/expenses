import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

function formatMoney(amount) {
  return `Rs. ${Number(amount).toFixed(2)}`;
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

export function downloadReportPdf({ period, userName, transactions }) {
  const income = transactions.filter((t) => t.type === "income").reduce((s, t) => s + t.amount, 0);
  const expenses = transactions.filter((t) => t.type === "expense").reduce((s, t) => s + t.amount, 0);

  const doc = new jsPDF();
  const title = `${PERIOD_LABEL[period]} Budget Report`;

  doc.setFontSize(16);
  doc.text(title, 14, 18);
  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`${userName} - generated ${new Date().toLocaleDateString()}`, 14, 25);

  doc.setFontSize(11);
  doc.setTextColor(20);
  doc.text(`Total Income: ${formatMoney(income)}`, 14, 36);
  doc.text(`Total Expenses: ${formatMoney(expenses)}`, 14, 43);
  doc.text(`Balance: ${formatMoney(income - expenses)}`, 14, 50);

  autoTable(doc, {
    startY: 58,
    head: [["Date", "Type", "Category", "Description", "Amount"]],
    body: transactions.map((t) => [
      t.date,
      t.type,
      t.category,
      t.description || "",
      formatMoney(t.amount),
    ]),
    styles: { fontSize: 9 },
    headStyles: { fillColor: [79, 70, 229] },
  });

  doc.save(`${period}-budget-report.pdf`);
}
