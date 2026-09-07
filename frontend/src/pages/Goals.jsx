import { useEffect, useState } from "react";

import { IconEdit, IconFlag, IconPlus, IconTrash } from "../components/icons";
import DatePicker from "../components/DatePicker";
import { useAuth } from "../context/AuthContext";
import { addGoalFunds, createGoal, deleteGoal, getGoals, updateGoal } from "../services/api";
import { fromBase, toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const EMPTY_FORM = { name: "", target_amount: "", target_date: "" };

function Goals() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [goals, setGoals] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [addAmounts, setAddAmounts] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null); // null = "add" mode

  function refresh() {
    setLoading(true);
    return getGoals(token)
      .then(setGoals)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function handleEdit(goal) {
    setEditingId(goal.id);
    setForm({
      name: goal.name,
      target_amount: fromBase(goal.target_amount, user.currency),
      target_date: goal.target_date || "",
    });
  }

  function handleCancelEdit() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      const payload = {
        ...form,
        target_amount: toBase(form.target_amount, user.currency),
        target_date: form.target_date || null,
      };
      if (editingId) {
        await updateGoal(editingId, payload, token);
        setEditingId(null);
      } else {
        await createGoal(payload, token);
      }
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAddFunds(id) {
    const amount = Number(addAmounts[id]);
    if (!amount || amount <= 0) return;
    setError(null);
    try {
      await addGoalFunds(id, amount, token);
      setAddAmounts((prev) => ({ ...prev, [id]: "" }));
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteGoal(id, token);
      if (editingId === id) handleCancelEdit();
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Goals</h1>
        <p>Save toward something specific and track progress over time.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Goal
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Emergency Fund"
              required
            />
          </label>
          <label>
            Target Amount
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={form.target_amount}
              onChange={(e) => setForm((f) => ({ ...f, target_amount: e.target.value }))}
              required
            />
          </label>
          <label>
            Target Date
            <DatePicker
              ariaLabel="Goal target date"
              value={form.target_date}
              onChange={(date) => setForm((f) => ({ ...f, target_date: date }))}
            />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            {editingId ? "Save Changes" : "Add Goal"}
          </button>
          {editingId && (
            <button type="button" className="link-btn" onClick={handleCancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading goals...</p>
      ) : goals.length === 0 ? (
        <div className="card empty-state">
          <IconFlag width={36} height={36} />
          <p>No goals yet — add one above to start saving toward it.</p>
        </div>
      ) : (
        <div className="account-card-grid">
          {goals.map((g) => {
            const percent = Math.min((g.current_amount / g.target_amount) * 100, 100);
            const reached = g.current_amount >= g.target_amount;
            return (
              <div className="card card-padded" key={g.id}>
                <div className="account-card-header">
                  <span className="category-badge">
                    <IconFlag width={13} height={13} />
                    {g.target_date || "No deadline"}
                  </span>
                  <button
                    type="button"
                    className="btn-icon"
                    onClick={() => handleEdit(g)}
                    aria-label={`Edit ${g.name}`}
                  >
                    <IconEdit width={15} height={15} />
                  </button>
                  <button
                    type="button"
                    className="btn-icon danger"
                    onClick={() => handleDelete(g.id)}
                    aria-label={`Delete ${g.name}`}
                  >
                    <IconTrash width={15} height={15} />
                  </button>
                </div>
                <div className="account-card-name">{g.name}</div>
                <div className="category-bar-label" style={{ marginTop: "0.75rem" }}>
                  <span>{formatMoney(g.current_amount)}</span>
                  <span>{formatMoney(g.target_amount)}</span>
                </div>
                <div className="category-bar-track">
                  <div
                    className="category-bar-fill"
                    style={{ width: `${percent}%`, background: reached ? "var(--color-income)" : undefined }}
                  />
                </div>
                {!reached && (
                  <div className="form-row" style={{ marginTop: "0.9rem" }}>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      placeholder="Add funds"
                      value={addAmounts[g.id] || ""}
                      onChange={(e) => setAddAmounts((prev) => ({ ...prev, [g.id]: e.target.value }))}
                    />
                    <button type="button" className="btn-secondary" onClick={() => handleAddFunds(g.id)}>
                      Add
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Goals;
