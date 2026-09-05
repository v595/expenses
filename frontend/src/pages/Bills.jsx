import { useEffect, useState } from "react";

import { BILL_TYPE_OPTIONS, billTypeIcon } from "../components/billIcons";
import { IconCheck, IconPlus, IconTrash } from "../components/icons";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import { createBill, deleteBill, getBills, payBill } from "../services/api";
import { toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const REPEAT_OPTIONS = [
  { value: "none", label: "Doesn't repeat" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

const EMPTY_FORM = {
  name: "",
  amount: "",
  due_date: new Date().toISOString().slice(0, 10),
  repeat_frequency: "none",
  bill_type: "",
};

function Bills() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [bills, setBills] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Choosing a type fills the name for you, unless you've typed your own.
  function handleTypeChange(bill_type) {
    const picked = BILL_TYPE_OPTIONS.find((t) => t.value === bill_type);
    setForm((f) => ({
      ...f,
      bill_type,
      name:
        !f.name || BILL_TYPE_OPTIONS.some((t) => t.label === f.name)
          ? picked?.label || ""
          : f.name,
    }));
  }

  function refresh() {
    setLoading(true);
    return getBills(token)
      .then(setBills)
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
      await createBill({ ...form, amount: toBase(form.amount, user.currency) }, token);
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handlePay(id) {
    setError(null);
    try {
      await payBill(id, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteBill(id, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Bills</h1>
        <p>One-off or repeating bills to pay, with reminders as the due date approaches.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Bill type
            <Select
              ariaLabel="Bill type"
              placeholder="Choose a type"
              value={form.bill_type}
              onChange={handleTypeChange}
              options={BILL_TYPE_OPTIONS}
            />
          </label>
          <label>
            Name
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Electricity"
              required
            />
          </label>
          <label>
            Amount
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount}
              onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
              required
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            Due Date
            <input
              type="date"
              value={form.due_date}
              onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))}
              required
            />
          </label>
          <label>
            Repeats
            <Select
              ariaLabel="Repeat frequency"
              value={form.repeat_frequency}
              onChange={(repeat_frequency) => setForm((f) => ({ ...f, repeat_frequency }))}
              options={REPEAT_OPTIONS}
            />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            Add Bill
          </button>
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading bills...</p>
      ) : bills.length === 0 ? (
        <div className="card empty-state">
          <p>No bills yet — add one above to get reminders before it's due.</p>
        </div>
      ) : (
        <div className="card transaction-list-card">
          <div className="table-scroll">
            <table className="transaction-list">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Amount</th>
                  <th>Due Date</th>
                  <th>Repeats</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {bills.map((b) => {
                  const overdue = !b.is_paid && b.due_date < today;
                  return (
                    <tr key={b.id}>
                      <td>
                        <span className="bill-name-cell">
                          <span className="bill-type-icon">{billTypeIcon(b.bill_type)}</span>
                          {b.name}
                        </span>
                      </td>
                      <td className="amount-cell expense">{formatMoney(b.amount)}</td>
                      <td style={overdue ? { color: "var(--color-expense)", fontWeight: 600 } : undefined}>
                        {b.due_date}
                      </td>
                      <td style={{ textTransform: "capitalize" }}>{b.repeat_frequency || "none"}</td>
                      <td>
                        {b.is_paid ? (
                          <span className="category-badge">Paid</span>
                        ) : overdue ? (
                          <span className="category-badge" style={{ color: "var(--color-expense)" }}>
                            Overdue
                          </span>
                        ) : (
                          <span className="category-badge">Pending</span>
                        )}
                      </td>
                      <td className="row-actions">
                        {!b.is_paid && (
                          <button
                            type="button"
                            className="btn-icon"
                            title="Mark as paid"
                            onClick={() => handlePay(b.id)}
                          >
                            <IconCheck width={16} height={16} />
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn-icon danger"
                          title="Delete"
                          onClick={() => handleDelete(b.id)}
                        >
                          <IconTrash width={16} height={16} />
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

export default Bills;
