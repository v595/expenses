import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import SummaryCard from "../components/SummaryCard";
import { IconReceipt, IconTrendingDown, IconTrendingUp, IconWallet } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import { getDashboardSummary, getTransactions } from "../services/api";
import { categoryColor } from "../utils/categoryColor";

function formatMoney(amount) {
  return `₹${amount.toFixed(2)}`;
}

function Dashboard() {
  const { token, user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [recent, setRecent] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getDashboardSummary(token), getTransactions(token)])
      .then(([summaryData, transactions]) => {
        setSummary(summaryData);
        setRecent(transactions.slice(0, 5));
      })
      .catch((err) => setError(err.message));
  }, [token]);

  if (error) return <p className="page error-message">{error}</p>;
  if (!summary) return <p className="page loading-state">Loading dashboard...</p>;

  const maxCategoryTotal = summary.category_spending[0]?.total || 1;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Welcome back, {user.name.split(" ")[0]}</h1>
        <p>Here's what's happening with your money.</p>
      </div>

      <div className="summary-grid">
        <SummaryCard
          label="Total Income"
          value={formatMoney(summary.income)}
          variant="income"
          icon={IconTrendingUp}
        />
        <SummaryCard
          label="Total Expenses"
          value={formatMoney(summary.expenses)}
          variant="expense"
          icon={IconTrendingDown}
        />
        <SummaryCard
          label="Balance"
          value={formatMoney(summary.balance)}
          variant="balance"
          icon={IconWallet}
        />
        <SummaryCard
          label="Transactions"
          value={summary.transaction_count}
          variant="count"
          icon={IconReceipt}
        />
      </div>

      <div className="dashboard-grid">
        <div className="card card-padded">
          <h2 className="card-title">Spending by Category</h2>
          {summary.category_spending.length === 0 ? (
            <p style={{ color: "var(--color-text-muted)", fontSize: "0.88rem", margin: 0 }}>
              No expenses recorded yet.
            </p>
          ) : (
            summary.category_spending.map((c) => (
              <div className="category-bar-row" key={c.category}>
                <div className="category-bar-label">
                  <span>{c.category}</span>
                  <span>{formatMoney(c.total)}</span>
                </div>
                <div className="category-bar-track">
                  <div
                    className="category-bar-fill"
                    style={{
                      width: `${(c.total / maxCategoryTotal) * 100}%`,
                      background: categoryColor(c.category),
                    }}
                  />
                </div>
              </div>
            ))
          )}
        </div>

        <div className="card card-padded">
          <h2 className="card-title">
            Recent Transactions
            <Link to="/transactions">View all</Link>
          </h2>
          {recent.length === 0 ? (
            <p style={{ color: "var(--color-text-muted)", fontSize: "0.88rem", margin: 0 }}>
              No transactions yet.
            </p>
          ) : (
            <ul className="recent-list">
              {recent.map((t) => (
                <li className="recent-item" key={t.id}>
                  <span className={`recent-item-icon ${t.type}`}>
                    {t.type === "income" ? (
                      <IconTrendingUp width={16} height={16} />
                    ) : (
                      <IconTrendingDown width={16} height={16} />
                    )}
                  </span>
                  <div className="recent-item-main">
                    <div className="recent-item-category">{t.category}</div>
                    <div className="recent-item-date">{t.date}</div>
                  </div>
                  <span className={`recent-item-amount ${t.type}`}>
                    {t.type === "expense" ? "-" : "+"}
                    {formatMoney(t.amount)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
