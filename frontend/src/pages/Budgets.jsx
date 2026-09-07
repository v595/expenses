import { useEffect, useState } from "react";

import { IconTrash, IconUser } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import {
  deleteBudget,
  getBudgetShares,
  getBudgets,
  getBudgetsSharedWithMe,
  setBudget,
  shareBudget,
  unshareBudget,
} from "../services/api";
import { toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

function Budgets() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [budgets, setBudgets] = useState([]);
  const [sharedWithMe, setSharedWithMe] = useState([]);
  const [form, setForm] = useState({ category: "", monthly_limit: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // category currently showing its share panel, plus that panel's own state
  const [sharingCategory, setSharingCategory] = useState(null);
  const [shares, setShares] = useState([]);
  const [shareEmail, setShareEmail] = useState("");

  function refresh() {
    setLoading(true);
    return Promise.all([getBudgets(token), getBudgetsSharedWithMe(token)])
      .then(([budgetsData, sharedData]) => {
        setBudgets(budgetsData);
        setSharedWithMe(sharedData);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  async function openSharePanel(category) {
    setError(null);
    if (sharingCategory === category) {
      setSharingCategory(null);
      return;
    }
    setSharingCategory(category);
    try {
      setShares(await getBudgetShares(category, token));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleShareSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      await shareBudget(sharingCategory, shareEmail, token);
      setShareEmail("");
      setShares(await getBudgetShares(sharingCategory, token));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUnshare(userId) {
    setError(null);
    try {
      await unshareBudget(sharingCategory, userId, token);
      setShares(await getBudgetShares(sharingCategory, token));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      await setBudget(form.category, toBase(form.monthly_limit, user.currency), token);
      setForm({ category: "", monthly_limit: "" });
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(category) {
    setError(null);
    try {
      await deleteBudget(category, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Budgets</h1>
        <p>Set a monthly spending limit per category and track it against this month's expenses.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Category
            <input
              type="text"
              placeholder="e.g. Food"
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
              required
            />
          </label>
          <label>
            Monthly Limit
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="e.g. 5000"
              value={form.monthly_limit}
              onChange={(e) => setForm((f) => ({ ...f, monthly_limit: e.target.value }))}
              required
            />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">Save Budget</button>
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading budgets...</p>
      ) : budgets.length === 0 ? (
        <div className="card empty-state">
          <p>No budgets set yet — add one above to start tracking.</p>
        </div>
      ) : (
        <div className="card card-padded">
          {budgets.map((b) => {
            const percent = Math.min((b.spent / b.monthly_limit) * 100, 100);
            const over = b.spent > b.monthly_limit;
            return (
              <div className="category-bar-row" key={b.category}>
                <div className="category-bar-label">
                  <span>{b.category}</span>
                  <span style={over ? { color: "var(--color-expense)" } : undefined}>
                    {formatMoney(b.spent)} / {formatMoney(b.monthly_limit)}
                    <button
                      type="button"
                      className="btn-icon"
                      onClick={() => openSharePanel(b.category)}
                      aria-label={`Share ${b.category} budget`}
                      style={{ marginLeft: "0.5rem" }}
                    >
                      <IconUser width={14} height={14} />
                    </button>
                    <button
                      type="button"
                      className="btn-icon danger"
                      onClick={() => handleDelete(b.category)}
                      aria-label={`Delete ${b.category} budget`}
                    >
                      <IconTrash width={14} height={14} />
                    </button>
                  </span>
                </div>
                <div className="category-bar-track">
                  <div
                    className="category-bar-fill"
                    style={{
                      width: `${percent}%`,
                      background: over ? "var(--color-expense)" : "var(--color-primary)",
                    }}
                  />
                </div>

                {sharingCategory === b.category && (
                  <div className="card card-padded" style={{ marginTop: "0.6rem" }}>
                    <p style={{ marginTop: 0, fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
                      Share "{b.category}" (read-only) with someone by their account email.
                    </p>
                    {shares.length > 0 && (
                      <div className="category-chip-list" style={{ marginBottom: "0.6rem" }}>
                        {shares.map((s) => (
                          <span key={s.user_id} className="category-chip">
                            {s.name}
                            <button
                              type="button"
                              className="chip-remove"
                              onClick={() => handleUnshare(s.user_id)}
                              aria-label={`Stop sharing with ${s.name}`}
                            >
                              <IconTrash width={12} height={12} />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                    <form className="form-row" onSubmit={handleShareSubmit}>
                      <input
                        type="email"
                        placeholder="person@example.com"
                        value={shareEmail}
                        onChange={(e) => setShareEmail(e.target.value)}
                        required
                      />
                      <button type="submit" className="btn-secondary">
                        Share
                      </button>
                    </form>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {sharedWithMe.length > 0 && (
        <div className="card card-padded">
          <h2 className="card-title">Shared with me</h2>
          {sharedWithMe.map((b) => {
            const percent = Math.min((b.spent / b.monthly_limit) * 100, 100);
            const over = b.spent > b.monthly_limit;
            return (
              <div className="category-bar-row" key={b.share_id}>
                <div className="category-bar-label">
                  <span>
                    {b.category} <span style={{ color: "var(--color-text-muted)" }}>(by {b.owner_name})</span>
                  </span>
                  <span style={over ? { color: "var(--color-expense)" } : undefined}>
                    {formatMoney(b.spent)} / {formatMoney(b.monthly_limit)}
                  </span>
                </div>
                <div className="category-bar-track">
                  <div
                    className="category-bar-fill"
                    style={{
                      width: `${percent}%`,
                      background: over ? "var(--color-expense)" : "var(--color-primary)",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Budgets;
