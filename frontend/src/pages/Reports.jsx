import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Select from "../components/Select";
import { IconDownload } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import {
  createRecurring,
  getDashboardMonthly,
  getDashboardSummary,
  getDetectedSubscriptions,
  getTransactions,
} from "../services/api";
import { categoryColor } from "../utils/categoryColor";
import { formatMoney as formatMoneyIn } from "../utils/currency";
import { downloadCategorySummaryCsv } from "../utils/downloadCsv";
import { downloadReportPdf, getFinancialYearRange } from "../utils/downloadReportPdf";

function monthLabel(monthStr) {
  const [year, month] = monthStr.split("-");
  const date = new Date(Number(year), Number(month) - 1, 1);
  return date.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
}

function CurrencyTooltip({ active, payload, label }) {
  const { user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "white",
        border: "1px solid var(--color-border)",
        borderRadius: 8,
        padding: "0.6rem 0.8rem",
        fontSize: "0.82rem",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name}: {formatMoney(entry.value)}
        </div>
      ))}
    </div>
  );
}

function Reports() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [monthly, setMonthly] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const currentFyStart = new Date().getMonth() >= 3 ? new Date().getFullYear() : new Date().getFullYear() - 1;
  const [fyStartYear, setFyStartYear] = useState(currentFyStart);
  // Which export is in flight — null | "csv" | "pdf" — so the CSV and PDF
  // buttons each show their own "Preparing..." state instead of the PDF
  // button reacting to a CSV click and vice versa.
  const [exporting, setExporting] = useState(null);
  const [subscriptions, setSubscriptions] = useState([]);
  const [trackingKey, setTrackingKey] = useState(null);

  useEffect(() => {
    Promise.all([getDashboardMonthly(token), getDashboardSummary(token)])
      .then(([monthlyData, summaryData]) => {
        setMonthly(monthlyData.monthly);
        setSummary(summaryData);
      })
      .catch((err) => setError(err.message));
    getDetectedSubscriptions(token)
      .then(setSubscriptions)
      .catch(() => {}); // non-critical — the rest of the page still works without it
  }, [token]);

  async function handleTrackSubscription(sub) {
    const key = `${sub.description}::${sub.amount}`;
    setTrackingKey(key);
    setError(null);
    try {
      await createRecurring(
        {
          amount: sub.amount,
          type: "expense",
          category: sub.category,
          description: sub.description,
          frequency: "monthly",
          start_date: new Date().toISOString().slice(0, 10),
        },
        token
      );
      setSubscriptions((prev) => prev.filter((s) => `${s.description}::${s.amount}` !== key));
    } catch (err) {
      setError(err.message);
    } finally {
      setTrackingKey(null);
    }
  }

  if (error) return <p className="page error-message">{error}</p>;
  if (!monthly || !summary) return <p className="page loading-state">Loading reports...</p>;

  if (monthly.length === 0) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>Reports</h1>
          <p>Income and expenses trended over time.</p>
        </div>
        <p style={{ color: "var(--color-text-muted)" }}>
          No transactions yet — add some to see reports here.
        </p>
      </div>
    );
  }

  const fyOptions = Array.from({ length: 6 }, (_, i) => currentFyStart - i).map((y) => ({
    value: y,
    label: `FY ${y}-${String(y + 1).slice(2)}`,
  }));

  async function handleExport(kind) {
    setExporting(kind);
    setError(null);
    try {
      const range = getFinancialYearRange(fyStartYear);
      const transactions = await getTransactions(token, range);
      const fyLabel = `FY${fyStartYear}-${String(fyStartYear + 1).slice(2)}`;
      if (kind === "pdf") {
        downloadReportPdf({
          period: "fy",
          userName: user.name,
          transactions,
          range,
          currency: user.currency,
          fileName: `${fyLabel}-tax-summary.pdf`,
        });
      } else {
        downloadCategorySummaryCsv(transactions, `${fyLabel}-category-summary.csv`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting(null);
    }
  }

  const chartData = monthly.map((m) => ({
    month: monthLabel(m.month),
    Income: m.income,
    Expenses: m.expenses,
  }));

  const pieData = summary.category_spending.map((c) => ({
    name: c.category,
    value: c.total,
  }));

  return (
    <div className="page">
      <div className="page-header">
        <h1>Reports</h1>
        <p>Income and expenses trended by month, and where your money goes.</p>
      </div>

      <div className="dashboard-grid">
        <div className="card card-padded">
          <h2 className="card-title">Monthly Income vs Expenses</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barGap={6} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} padding={{ left: 20, right: 20 }} />
              <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
              <Tooltip content={<CurrencyTooltip />} cursor={{ fill: "var(--color-bg)" }} />
              <Legend wrapperStyle={{ fontSize: "0.82rem" }} />
              <Bar dataKey="Income" fill="var(--color-income)" radius={[4, 4, 0, 0]} maxBarSize={48} />
              <Bar dataKey="Expenses" fill="var(--color-expense)" radius={[4, 4, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card card-padded">
          <h2 className="card-title">Spending by Category</h2>
          {pieData.length === 0 ? (
            <p style={{ color: "var(--color-text-muted)", fontSize: "0.88rem" }}>
              No expenses recorded yet.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={categoryColor(entry.name)} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatMoney(value)} />
                <Legend wrapperStyle={{ fontSize: "0.82rem" }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card card-padded">
        <div className="profile-card-head">
          <h2 className="card-title">Tax / Financial Year Export</h2>
          <p>Category totals and full transaction detail for one financial year (Apr–Mar), ready to hand to an accountant.</p>
        </div>
        {error && <p className="error-message">{error}</p>}
        <div className="form-row" style={{ alignItems: "flex-end" }}>
          <label style={{ maxWidth: 220 }}>
            Financial Year
            <Select
              ariaLabel="Financial year"
              value={fyStartYear}
              onChange={(value) => setFyStartYear(Number(value))}
              options={fyOptions}
            />
          </label>
          <button
            type="button"
            className="btn-secondary"
            disabled={Boolean(exporting)}
            onClick={() => handleExport("csv")}
          >
            <IconDownload width={16} height={16} />
            {exporting === "csv" ? "Preparing..." : "Category Summary (CSV)"}
          </button>
          <button type="button" disabled={Boolean(exporting)} onClick={() => handleExport("pdf")}>
            <IconDownload width={16} height={16} />
            {exporting === "pdf" ? "Preparing..." : "Full Tax Report (PDF)"}
          </button>
        </div>
      </div>

      {subscriptions.length > 0 && (
        <div className="card card-padded">
          <div className="profile-card-head">
            <h2 className="card-title">Subscription Radar</h2>
            <p>Charges that look recurring but aren't tracked as a Recurring rule yet.</p>
          </div>
          <div className="table-scroll">
            <table className="transaction-list">
              <thead>
                <tr>
                  <th>Description</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Seen</th>
                  <th>Est. yearly</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {subscriptions.map((sub) => {
                  const key = `${sub.description}::${sub.amount}`;
                  return (
                    <tr key={key}>
                      <td>{sub.description}</td>
                      <td>{sub.category}</td>
                      <td className="amount-cell expense">{formatMoney(sub.amount)}</td>
                      <td>{sub.months_seen}mo</td>
                      <td className="amount-cell expense">{formatMoney(sub.estimated_yearly_cost)}</td>
                      <td className="row-actions">
                        <button
                          type="button"
                          className="btn-secondary"
                          disabled={trackingKey === key}
                          onClick={() => handleTrackSubscription(sub)}
                        >
                          {trackingKey === key ? "Adding..." : "Track as Recurring"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reports;
