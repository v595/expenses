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

import { useAuth } from "../context/AuthContext";
import { getDashboardMonthly, getDashboardSummary } from "../services/api";
import { categoryColor } from "../utils/categoryColor";

function formatMoney(amount) {
  return `₹${amount.toFixed(2)}`;
}

function monthLabel(monthStr) {
  const [year, month] = monthStr.split("-");
  const date = new Date(Number(year), Number(month) - 1, 1);
  return date.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
}

function CurrencyTooltip({ active, payload, label }) {
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
  const { token } = useAuth();
  const [monthly, setMonthly] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getDashboardMonthly(token), getDashboardSummary(token)])
      .then(([monthlyData, summaryData]) => {
        setMonthly(monthlyData.monthly);
        setSummary(summaryData);
      })
      .catch((err) => setError(err.message));
  }, [token]);

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
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} width={40} />
              <Tooltip content={<CurrencyTooltip />} cursor={{ fill: "var(--color-bg)" }} />
              <Legend wrapperStyle={{ fontSize: "0.82rem" }} />
              <Bar dataKey="Income" fill="var(--color-income)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Expenses" fill="var(--color-expense)" radius={[4, 4, 0, 0]} />
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
    </div>
  );
}

export default Reports;
