import { useEffect, useState } from "react";

import { IconPlus, IconTrash } from "../components/icons";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import { createRecurring, deleteRecurring, getRecurring } from "../services/api";
import { toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const EMPTY_FORM = {
  amount: "",
  type: "expense",
  category: "",
  description: "",
  frequency: "monthly",
  start_date: new Date().toISOString().slice(0, 10),
};

function Recurring() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [rules, setRules] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  function refresh() {
    setLoading(true);
    return getRecurring(token)
      .then(setRules)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      await createRecurring({ ...form, amount: toBase(form.amount, user.currency) }, token);
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteRecurring(id, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Recurring Transactions</h1>
        <p>Set it once — rent, salary, subscriptions get logged automatically on schedule.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form className="card transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Amount
            <input
              type="number"
              name="amount"
              value={form.amount}
              onChange={handleChange}
              min="0.01"
              step="0.01"
              required
            />
          </label>
          <label>
            Type
            <Select
              ariaLabel="Type"
              value={form.type}
              onChange={(value) => handleChange({ target: { name: "type", value } })}
              options={[
                { value: "expense", label: "Expense" },
                { value: "income", label: "Income" },
              ]}
            />
          </label>
        </div>

        <div className="form-row">
          <label>
            Category
            <input
              type="text"
              name="category"
              value={form.category}
              onChange={handleChange}
              placeholder="Rent, Salary, Netflix..."
              required
            />
          </label>
          <label>
            Frequency
            <Select
              ariaLabel="Frequency"
              value={form.frequency}
              onChange={(value) => handleChange({ target: { name: "frequency", value } })}
              options={[
                { value: "weekly", label: "Weekly" },
                { value: "monthly", label: "Monthly" },
                { value: "yearly", label: "Yearly" },
              ]}
            />
          </label>
        </div>

        <div className="form-row">
          <label>
            Starts On
            <input
              type="date"
              name="start_date"
              value={form.start_date}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Description
            <input
              type="text"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Optional"
            />
          </label>
        </div>

        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            Add Recurring Rule
          </button>
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading recurring transactions...</p>
      ) : rules.length === 0 ? (
        <div className="card empty-state">
          <p>No recurring transactions set up yet.</p>
        </div>
      ) : (
        <div className="card transaction-list-card">
          <div className="table-scroll">
            <table className="transaction-list">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Frequency</th>
                  <th>Next Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r) => (
                  <tr key={r.id}>
                    <td>{r.category}</td>
                    <td>{r.type}</td>
                    <td className={`amount-cell ${r.type}`}>{formatMoney(r.amount)}</td>
                    <td style={{ textTransform: "capitalize" }}>{r.frequency}</td>
                    <td>{r.next_date}</td>
                    <td className="row-actions">
                      <button
                        type="button"
                        className="btn-icon danger"
                        onClick={() => handleDelete(r.id)}
                        aria-label={`Delete ${r.category} recurring rule`}
                      >
                        <IconTrash width={16} height={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recurring;
