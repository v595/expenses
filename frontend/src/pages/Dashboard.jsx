import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import SummaryCard from "../components/SummaryCard";
import { IconDownload, IconReceipt, IconTrendingDown, IconTrendingUp, IconWallet } from "../components/icons";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import { getDashboardInsights, getDashboardSummary, getTransactions } from "../services/api";
import { categoryColor } from "../utils/categoryColor";
import { formatMoney as formatMoneyIn } from "../utils/currency";
import { downloadReportPdf, getRangeForPeriod } from "../utils/downloadReportPdf";

function Dashboard() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [summary, setSummary] = useState(null);
  const [recent, setRecent] = useState([]);
  const [insights, setInsights] = useState(null);
  const [error, setError] = useState(null);
  const [reportPeriod, setReportPeriod] = useState("month");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    Promise.all([getDashboardSummary(token), getTransactions(token), getDashboardInsights(token)])
      .then(([summaryData, transactions, insightsData]) => {
        setSummary(summaryData);
        setRecent(transactions.slice(0, 5));
        setInsights(insightsData);
      })
      .catch((err) => setError(err.message));
  }, [token]);

  if (error) return <p className="page error-message">{error}</p>;
  if (!summary) return <p className="page loading-state">Loading dashboard...</p>;

  const maxCategoryTotal = summary.category_spending[0]?.total || 1;

  async function handleDownload() {
    setDownloading(true);
    try {
      const range = getRangeForPeriod(reportPeriod);
      const transactions = await getTransactions(token, range);
      downloadReportPdf({ period: reportPeriod, userName: user.name, transactions, range, currency: user.currency });
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header dashboard-header">
        <div>
          <h1>Welcome back, {user.name.split(" ")[0]}</h1>
          <p>Here's what's happening with your money.</p>
        </div>
        <div className="report-download">
          <Select
            ariaLabel="Report period"
            value={reportPeriod}
            onChange={setReportPeriod}
            options={[
              { value: "week", label: "Weekly" },
              { value: "month", label: "Monthly" },
              { value: "year", label: "Yearly" },
            ]}
          />
          <button type="button" onClick={handleDownload} disabled={downloading}>
            <IconDownload width={16} height={16} />
            {downloading ? "Preparing..." : "Download PDF"}
          </button>
        </div>
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

      {insights && insights.movers.length > 0 && (
        <div className="card card-padded" style={{ marginBottom: "1.25rem" }}>
          <h2 className="card-title">Insights</h2>
          <ul className="insights-list">
            {insights.movers.map((m) => (
              <li key={m.category} className="insights-item">
                {m.change > 0 ? (
                  <IconTrendingUp width={16} height={16} className="insights-icon-up" />
                ) : (
                  <IconTrendingDown width={16} height={16} className="insights-icon-down" />
                )}
                <span>
                  <strong>{m.category}</strong> is {m.change > 0 ? "up" : "down"}{" "}
                  {Math.abs(m.percent_change).toFixed(0)}% vs last month (
                  {formatMoney(m.previous)} → {formatMoney(m.current)})
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

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
