import { useEffect, useRef, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { getAccounts } from "../services/api";
import { IconPlus, IconUpload } from "./icons";
import Select from "./Select";
import { fromBase, toBase } from "../utils/fx";
import { scanReceiptForAmount } from "../utils/ocrReceipt";

const MAX_RECEIPT_BYTES = 2 * 1024 * 1024;

const TYPE_OPTIONS = [
  { value: "expense", label: "Expense" },
  { value: "income", label: "Income" },
];

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

function toFormValues(initialValues, currency) {
  if (!initialValues) return emptyForm();
  return {
    ...initialValues,
    // Stored in the base currency, but the field is edited in the currency
    // on screen — otherwise editing a row would show a different number than
    // the list did, and saving would silently re-scale it.
    amount: round2(fromBase(initialValues.amount, currency)),
    account_id: initialValues.account_id ?? "",
    tags: (initialValues.tags || []).map((t) => t.name).join(", "),
    receipt: initialValues.receipt ?? null,
  };
}

function round2(n) {
  return Math.round(Number(n) * 100) / 100;
}

// initialValues lets this same form be reused for both "add" and "edit".
// prefillValues seeds the "add" form (e.g. from a parsed bank SMS or a
// receipt scan) without switching it into edit mode — it's already in the
// currency shown on screen, unlike initialValues which is stored/base
// currency. onSubmit is a callback prop — the parent decides what actually
// happens with the data (in Phase 6: log it; in Phase 7: send it to the API).
function TransactionForm({ initialValues, prefillValues, onSubmit, onCancel }) {
  const { token, user } = useAuth();
  const [form, setForm] = useState(() =>
    initialValues
      ? toFormValues(initialValues, user?.currency)
      : { ...emptyForm(), ...prefillValues }
  );
  const [accounts, setAccounts] = useState([]);
  const [ocrStatus, setOcrStatus] = useState(null); // null | "scanning" | "found" | "not-found"
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

    setOcrStatus(null);
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result;
      setForm((prev) => ({ ...prev, receipt: dataUrl }));

      // Only scan for an amount if the field is still empty — never
      // overwrite a number the user already typed or already reviewed.
      setForm((prev) => {
        if (prev.amount) return prev;
        setOcrStatus("scanning");
        scanReceiptForAmount(dataUrl).then((result) => {
          if (result.amount) {
            setForm((f) => (f.amount ? f : { ...f, amount: String(result.amount) }));
            setOcrStatus("found");
          } else {
            setOcrStatus("not-found");
          }
        });
        return prev;
      });
    };
    reader.readAsDataURL(file);
  }

  function handleSubmit(event) {
    event.preventDefault(); // stop the browser's default full-page reload on submit
    onSubmit({
      ...form,
      // Typed in whatever currency is on screen; stored in the base currency.
      amount: toBase(form.amount, user?.currency),
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
          <Select
            ariaLabel="Transaction type"
            value={form.type}
            onChange={(type) => handleChange({ target: { name: "type", value: type } })}
            options={TYPE_OPTIONS}
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
          <Select
            ariaLabel="Account"
            value={form.account_id}
            onChange={(id) => handleChange({ target: { name: "account_id", value: id } })}
            options={[
              { value: "", label: "No account" },
              ...accounts.map((a) => ({ value: String(a.id), label: a.name })),
            ]}
          />
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
        {ocrStatus === "scanning" && (
          <p className="loading-state" style={{ marginTop: "0.4rem" }}>
            Scanning receipt for the amount...
          </p>
        )}
        {ocrStatus === "found" && (
          <p className="success-message" style={{ marginTop: "0.4rem" }}>
            Found an amount on the receipt — double-check it above before saving.
          </p>
        )}
        {ocrStatus === "not-found" && (
          <p style={{ marginTop: "0.4rem", fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
            Couldn't read an amount off the receipt — enter it above.
          </p>
        )}
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
