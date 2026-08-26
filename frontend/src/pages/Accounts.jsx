import { useEffect, useState } from "react";

import { IconPlus, IconTrash, IconWalletStack } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import { createAccount, deleteAccount, getAccounts } from "../services/api";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const TYPES = ["cash", "bank", "card", "savings", "other"];
const EMPTY_FORM = { name: "", type: "cash", balance: "" };

function Accounts() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);
  const [accounts, setAccounts] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

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
      await createAccount({ ...form, balance: form.balance ? Number(form.balance) : 0 }, token);
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
            Name
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. HDFC Checking"
              required
            />
          </label>
          <label>
            Type
            <select value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}>
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t[0].toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
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
