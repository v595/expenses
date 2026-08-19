import { useEffect, useState } from "react";

import SummaryCard from "../components/SummaryCard";
import { useAuth } from "../context/AuthContext";
import { getDashboardSummary } from "../services/api";

function formatMoney(amount) {
  return `₹${amount.toFixed(2)}`;
}

function Dashboard() {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboardSummary(token)
      .then(setSummary)
      .catch((err) => setError(err.message));
  }, [token]);

  if (error) return <p className="page error-message">{error}</p>;
  if (!summary) return <p className="page">Loading...</p>;

  return (
    <div className="page">
      <h1>Dashboard</h1>
      <div className="summary-grid">
        <SummaryCard label="Total Income" value={formatMoney(summary.income)} variant="income" />
        <SummaryCard label="Total Expenses" value={formatMoney(summary.expenses)} variant="expense" />
        <SummaryCard label="Balance" value={formatMoney(summary.balance)} variant="balance" />
        <SummaryCard label="Transactions" value={summary.transaction_count} variant="count" />
      </div>

      {summary.top_category && (
        <p className="top-category">
          Top spending category: <strong>{summary.top_category.category}</strong> (
          {formatMoney(summary.top_category.total)})
        </p>
      )}

      {summary.category_spending.length > 0 && (
        <>
          <h2>Spending by Category</h2>
          <ul className="category-list">
            {summary.category_spending.map((c) => (
              <li key={c.category}>
                <span>{c.category}</span>
                <span>{formatMoney(c.total)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export default Dashboard;
