import { useEffect, useState } from "react";

import { IconTrash } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import { deleteBudget, getBudgets, setBudget } from "../services/api";

function formatMoney(amount) {
  return `₹${amount.toFixed(2)}`;
}

function Budgets() {
  const { token } = useAuth();
  const [budgets, setBudgets] = useState([]);
  const [form, setForm] = useState({ category: "", monthly_limit: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  function refresh() {
    setLoading(true);
    return getBudgets(token)
      .then(setBudgets)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      await setBudget(form.category, Number(form.monthly_limit), token);
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
                      className="btn-icon danger"
                      onClick={() => handleDelete(b.category)}
                      aria-label={`Delete ${b.category} budget`}
                      style={{ marginLeft: "0.5rem" }}
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
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Budgets;
