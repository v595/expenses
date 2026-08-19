import { useState } from "react";

import { IconPlus } from "./icons";

const EMPTY_FORM = {
  amount: "",
  type: "expense",
  category: "",
  description: "",
  date: new Date().toISOString().slice(0, 10),
};

// initialValues lets this same form be reused for both "add" and "edit".
// onSubmit is a callback prop — the parent decides what actually happens
// with the data (in Phase 6: log it; in Phase 7: send it to the API).
function TransactionForm({ initialValues, onSubmit, onCancel }) {
  const [form, setForm] = useState(initialValues || EMPTY_FORM);

  // A single change handler for every field, using the input's `name`
  // attribute to know which piece of state to update.
  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault(); // stop the browser's default full-page reload on submit
    onSubmit({ ...form, amount: Number(form.amount) });
    if (!initialValues) {
      setForm(EMPTY_FORM); // reset the form after adding a new transaction
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
