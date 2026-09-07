import { useEffect, useState } from "react";

import { IconEdit, IconPlus, IconTrash } from "../components/icons";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import { createCategory, deleteCategory, getCategories, updateCategory } from "../services/api";

const SWATCHES = ["#4f46e5", "#0891b2", "#d97706", "#db2777", "#65a30d", "#7c3aed", "#0d9488", "#ea580c"];

const EMPTY_FORM = { name: "", type: "expense", color: SWATCHES[0] };

function Categories() {
  const { token } = useAuth();
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null); // null = "add" mode

  function refresh() {
    setLoading(true);
    return getCategories(token)
      .then(setCategories)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function handleEdit(category) {
    setEditingId(category.id);
    setForm({ name: category.name, type: category.type, color: category.color || SWATCHES[0] });
  }

  function handleCancelEdit() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      if (editingId) {
        // Type is fixed once created — only name/color are sent.
        await updateCategory(editingId, { name: form.name, color: form.color }, token);
        setEditingId(null);
      } else {
        await createCategory(form, token);
      }
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteCategory(id, token);
      if (editingId === id) handleCancelEdit();
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  const income = categories.filter((c) => c.type === "income");
  const expense = categories.filter((c) => c.type === "expense");

  return (
    <div className="page">
      <div className="page-header">
        <h1>Categories</h1>
        <p>Custom categories with colors — the amount and category fields on transactions accept any text, but these show up as quick suggestions.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Name
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Groceries"
              required
            />
          </label>
          <label>
            Type
            <Select
              ariaLabel="Category type"
              value={form.type}
              onChange={(type) => setForm((f) => ({ ...f, type }))}
              disabled={Boolean(editingId)}
              options={[
                { value: "expense", label: "Expense" },
                { value: "income", label: "Income" },
              ]}
            />
          </label>
        </div>
        <label>
          Color
          <div className="swatch-row">
            {SWATCHES.map((color) => (
              <button
                key={color}
                type="button"
                className="swatch"
                data-active={form.color === color}
                style={{ background: color }}
                onClick={() => setForm((f) => ({ ...f, color }))}
                aria-label={`Choose color ${color}`}
              />
            ))}
          </div>
        </label>
        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            {editingId ? "Save Changes" : "Add Category"}
          </button>
          {editingId && (
            <button type="button" className="link-btn" onClick={handleCancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading categories...</p>
      ) : (
        <div className="dashboard-grid">
          <div className="card card-padded">
            <h2 className="card-title">Income Categories</h2>
            {income.length === 0 ? (
              <p style={{ color: "var(--color-text-muted)", fontSize: "0.88rem" }}>None yet.</p>
            ) : (
              <div className="category-chip-list">
                {income.map((c) => (
                  <span key={c.id} className="category-chip">
                    <button
                      type="button"
                      className="chip-edit"
                      onClick={() => handleEdit(c)}
                      aria-label={`Edit ${c.name}`}
                    >
                      <span className="category-dot" style={{ background: c.color || "#4f46e5" }} />
                      {c.name}
                    </button>
                    <button
                      type="button"
                      className="chip-remove"
                      onClick={() => handleDelete(c.id)}
                      aria-label={`Delete ${c.name}`}
                    >
                      <IconTrash width={12} height={12} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="card card-padded">
            <h2 className="card-title">Expense Categories</h2>
            {expense.length === 0 ? (
              <p style={{ color: "var(--color-text-muted)", fontSize: "0.88rem" }}>None yet.</p>
            ) : (
              <div className="category-chip-list">
                {expense.map((c) => (
                  <span key={c.id} className="category-chip">
                    <button
                      type="button"
                      className="chip-edit"
                      onClick={() => handleEdit(c)}
                      aria-label={`Edit ${c.name}`}
                    >
                      <span className="category-dot" style={{ background: c.color || "#4f46e5" }} />
                      {c.name}
                    </button>
                    <button
                      type="button"
                      className="chip-remove"
                      onClick={() => handleDelete(c.id)}
                      aria-label={`Delete ${c.name}`}
                    >
                      <IconTrash width={12} height={12} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Categories;
