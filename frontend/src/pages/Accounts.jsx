import { useEffect, useState } from "react";

import { IconPlus, IconTrash, IconWalletStack } from "../components/icons";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import { ALL_ACCOUNT_SOURCES } from "../data/banks";
import { createAccount, deleteAccount, getAccounts } from "../services/api";
import { toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const TYPES = ["cash", "bank", "card", "savings", "other"];
const EMPTY_FORM = { name: "", type: "cash", balance: "", source: "" };

const TYPE_OPTIONS = TYPES.map((t) => ({
  value: t,
  label: t[0].toUpperCase() + t.slice(1),
}));

// Tinted initials rather than the real bank logo — see the note in data/banks.js.
function BankBadge({ short, color }) {
  return (
    <span className="bank-badge" style={{ background: color }} aria-hidden="true">
      {short}
    </span>
  );
}

const SOURCE_OPTIONS = ALL_ACCOUNT_SOURCES.map((b) => ({
  value: b.value,
  label: b.label,
  icon: <BankBadge short={b.short} color={b.color} />,
}));

// Picking a bank pre-fills the account name and the closest matching type, so
// the common case is one choice instead of three fields.
const SOURCE_TYPE = { cash: "cash", upi: "cash", credit_card: "card" };

function Accounts() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [accounts, setAccounts] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  function handleSourceChange(source) {
    const picked = ALL_ACCOUNT_SOURCES.find((b) => b.value === source);
    setForm((f) => ({
      ...f,
      source,
      type: SOURCE_TYPE[source] || "bank",
      // Only auto-fill while the name is still untouched or was filled by a
      // previous pick, so we never overwrite something typed by hand.
      name:
        !f.name || ALL_ACCOUNT_SOURCES.some((b) => b.label === f.name)
          ? picked?.label || ""
          : f.name,
    }));
  }

  function refresh() {
    setLoading(true);
    return getAccounts(token)
      .then(setAccounts)
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
      await createAccount(
        { ...form, balance: form.balance ? toBase(form.balance, user.currency) : 0 },
        token
      );
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteAccount(id, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  const totalBalance = accounts.reduce((sum, a) => sum + a.balance, 0);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Accounts</h1>
        <p>Track balances across cash, bank, and card accounts. Assign a transaction to one and its balance updates automatically.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Bank / Source
            <Select
              ariaLabel="Bank or account source"
              placeholder="Choose a bank"
              value={form.source}
              onChange={handleSourceChange}
              options={SOURCE_OPTIONS}
            />
          </label>
          <label>
            Account name
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Salary account"
              required
            />
          </label>
          <label>
            Type
            <Select
              ariaLabel="Account type"
              value={form.type}
              onChange={(type) => setForm((f) => ({ ...f, type }))}
              options={TYPE_OPTIONS}
            />
          </label>
          <label>
            Starting Balance
            <input
              type="number"
              step="0.01"
              value={form.balance}
              onChange={(e) => setForm((f) => ({ ...f, balance: e.target.value }))}
              placeholder="0.00"
            />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            Add Account
          </button>
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading accounts...</p>
      ) : accounts.length === 0 ? (
        <div className="card empty-state">
          <IconWalletStack width={36} height={36} />
          <p>No accounts yet — add one above to start tracking balances.</p>
        </div>
      ) : (
        <>
          <div className="summary-grid">
            <div className="card summary-card summary-card--balance">
              <span className="summary-card-icon">
                <IconWalletStack width={20} height={20} />
              </span>
              <div>
                <p className="summary-card-label">Total Across Accounts</p>
                <p className="summary-card-value">{formatMoney(totalBalance)}</p>
              </div>
            </div>
          </div>

          <div className="account-card-grid">
            {accounts.map((a) => (
              <div className="card card-padded account-card" key={a.id}>
                <div className="account-card-header">
                  <span className="category-badge" style={{ textTransform: "capitalize" }}>
                    {a.type}
                  </span>
                  <button
                    type="button"
                    className="btn-icon danger"
                    onClick={() => handleDelete(a.id)}
                    aria-label={`Delete ${a.name}`}
                  >
                    <IconTrash width={15} height={15} />
                  </button>
                </div>
                <div className="account-card-name">{a.name}</div>
                <div className={`account-card-balance ${a.balance < 0 ? "expense" : ""}`}>
                  {formatMoney(a.balance)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default Accounts;
