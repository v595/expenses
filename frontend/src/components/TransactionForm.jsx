import { useEffect, useRef, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { getAccounts } from "../services/api";
import { IconPlus, IconUpload } from "./icons";

const MAX_RECEIPT_BYTES = 2 * 1024 * 1024;

function emptyForm() {
  return {
    amount: "",
    type: "expense",
    category: "",
    description: "",
    date: new Date().toISOString().slice(0, 10),
    account_id: "",
    tags: "",
    receipt: null,
  };
}

function toFormValues(initialValues) {
  if (!initialValues) return emptyForm();
  return {
    ...initialValues,
    account_id: initialValues.account_id ?? "",
    tags: (initialValues.tags || []).map((t) => t.name).join(", "),
    receipt: initialValues.receipt ?? null,
  };
}

// initialValues lets this same form be reused for both "add" and "edit".
// onSubmit is a callback prop — the parent decides what actually happens
// with the data (in Phase 6: log it; in Phase 7: send it to the API).
function TransactionForm({ initialValues, onSubmit, onCancel }) {
  const { token } = useAuth();
  const [form, setForm] = useState(() => toFormValues(initialValues));
  const [accounts, setAccounts] = useState([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    getAccounts(token).then(setAccounts).catch(() => {});
  }, [token]);

  // A single change handler for every field, using the input's `name`
  // attribute to know which piece of state to update.
  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleReceiptChange(event) {
    const file = event.target.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) return;
    if (file.size > MAX_RECEIPT_BYTES) return;

    const reader = new FileReader();
    reader.onload = () => setForm((prev) => ({ ...prev, receipt: reader.result }));
    reader.readAsDataURL(file);
  }

  function handleSubmit(event) {
    event.preventDefault(); // stop the browser's default full-page reload on submit
    onSubmit({
      ...form,
      amount: Number(form.amount),
      account_id: form.account_id ? Number(form.account_id) : null,
      tags: form.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    });
    if (!initialValues) {
      setForm(emptyForm()); // reset the form after adding a new transaction
    }
  }

  return (
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
          <select name="type" value={form.type} onChange={handleChange}>
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
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
            placeholder="Food, Salary, Transport..."
            required
          />
        </label>

        <label>
          Date
          <input type="date" name="date" value={form.date} onChange={handleChange} required />
        </label>
      </div>

      <div className="form-row">
        <label>
          Account
          <select name="account_id" value={form.account_id} onChange={handleChange}>
            <option value="">No account</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Tags
          <input
            type="text"
            name="tags"
            value={form.tags}
            onChange={handleChange}
            placeholder="work, reimbursable"
          />
        </label>
      </div>

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

      <label>
        Receipt
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleReceiptChange}
          style={{ display: "none" }}
        />
        <div className="form-actions" style={{ marginTop: 0 }}>
          <button type="button" className="btn-secondary" onClick={() => fileInputRef.current.click()}>
            <IconUpload width={15} height={15} />
            {form.receipt ? "Replace Receipt" : "Attach Receipt"}
          </button>
          {form.receipt && (
            <img src={form.receipt} alt="Receipt preview" className="receipt-thumb" />
          )}
        </div>
      </label>

      <div className="form-actions">
        <button type="submit">
          {!initialValues && <IconPlus width={16} height={16} />}
          {initialValues ? "Save Changes" : "Add Transaction"}
        </button>
        {onCancel && (
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

export default TransactionForm;
