import { useEffect, useState } from "react";

import { IconEdit, IconPlus, IconTrash } from "../components/icons";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import { createDebt, deleteDebt, getDebtPayoffPlan, getDebts, updateDebt } from "../services/api";
import { fromBase, toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const EMPTY_FORM = { name: "", balance: "", interest_rate: "", min_payment: "" };

function monthsToYearsLabel(months) {
  const y = Math.floor(months / 12);
  const m = months % 12;
  if (y === 0) return `${m} mo`;
  if (m === 0) return `${y} yr`;
  return `${y} yr ${m} mo`;
}

function DebtPayoff() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);

  const [debts, setDebts] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const [strategy, setStrategy] = useState("avalanche");
  const [extraPayment, setExtraPayment] = useState("0");
  const [plan, setPlan] = useState(null);
  const [calculating, setCalculating] = useState(false);

  function refresh() {
    setLoading(true);
    return getDebts(token)
      .then(setDebts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function handleEdit(debt) {
    setEditingId(debt.id);
    setForm({
      name: debt.name,
      balance: fromBase(debt.balance, user.currency),
      interest_rate: debt.interest_rate,
      min_payment: fromBase(debt.min_payment, user.currency),
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
        name: form.name,
        balance: toBase(form.balance, user.currency),
        interest_rate: Number(form.interest_rate) || 0,
        min_payment: toBase(form.min_payment, user.currency),
      };
      if (editingId) {
        await updateDebt(editingId, payload, token);
        setEditingId(null);
      } else {
        await createDebt(payload, token);
      }
      setForm(EMPTY_FORM);
      setPlan(null);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteDebt(id, token);
      if (editingId === id) handleCancelEdit();
      setPlan(null);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCalculate() {
    setError(null);
    setCalculating(true);
    try {
      const data = await getDebtPayoffPlan(
        { strategy, extra_payment: toBase(extraPayment || 0, user.currency) },
        token
      );
      setPlan(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setCalculating(false);
    }
  }

  const totalMinPayment = debts.reduce((sum, d) => sum + d.min_payment, 0);
  const totalBalance = debts.reduce((sum, d) => sum + d.balance, 0);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Debt Payoff Planner</h1>
        <p>List what you owe, pick a strategy, and see exactly when you'll be debt-free.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Debt name
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Credit Card"
              required
            />
          </label>
          <label>
            Balance
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={form.balance}
              onChange={(e) => setForm((f) => ({ ...f, balance: e.target.value }))}
              required
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            Interest rate (% APR)
            <input
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={form.interest_rate}
              onChange={(e) => setForm((f) => ({ ...f, interest_rate: e.target.value }))}
              required
            />
          </label>
          <label>
            Minimum monthly payment
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={form.min_payment}
              onChange={(e) => setForm((f) => ({ ...f, min_payment: e.target.value }))}
              required
            />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            {editingId ? "Save Changes" : "Add Debt"}
          </button>
          {editingId && (
            <button type="button" className="link-btn" onClick={handleCancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading debts...</p>
      ) : debts.length === 0 ? (
        <div className="card empty-state">
          <p>No debts added yet — add one above to build a payoff plan.</p>
        </div>
      ) : (
        <div className="card transaction-list-card">
          <div className="table-scroll">
            <table className="transaction-list">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Balance</th>
                  <th>APR</th>
                  <th>Min Payment</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {debts.map((d) => (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td className="amount-cell expense">{formatMoney(d.balance)}</td>
                    <td>{d.interest_rate}%</td>
                    <td>{formatMoney(d.min_payment)}</td>
                    <td className="row-actions">
                      <button type="button" className="btn-icon" onClick={() => handleEdit(d)} aria-label={`Edit ${d.name}`}>
                        <IconEdit width={16} height={16} />
                      </button>
                      <button
                        type="button"
                        className="btn-icon danger"
                        onClick={() => handleDelete(d.id)}
                        aria-label={`Delete ${d.name}`}
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

      {debts.length > 0 && (
        <div className="card card-padded">
          <div className="profile-card-head">
            <h2 className="card-title">Build a payoff plan</h2>
            <p>
              Total owed {formatMoney(totalBalance)} across {debts.length} debt(s), minimum payments total{" "}
              {formatMoney(totalMinPayment)}/month.
            </p>
          </div>
          <div className="form-row" style={{ alignItems: "flex-end" }}>
            <label>
              Strategy
              <Select
                ariaLabel="Payoff strategy"
                value={strategy}
                onChange={setStrategy}
                options={[
                  { value: "avalanche", label: "Avalanche (highest interest first — least total interest)" },
                  { value: "snowball", label: "Snowball (smallest balance first — quick wins)" },
                ]}
              />
            </label>
            <label>
              Extra payment / month
              <input
                type="number"
                min="0"
                step="0.01"
                value={extraPayment}
                onChange={(e) => setExtraPayment(e.target.value)}
              />
            </label>
            <button type="button" onClick={handleCalculate} disabled={calculating}>
              {calculating ? "Calculating..." : "Calculate"}
            </button>
          </div>

          {plan && (
            <>
              <div className="summary-grid" style={{ marginTop: "1rem" }}>
                <div className="card summary-card summary-card--balance">
                  <div>
                    <p className="summary-card-label">Debt-free in</p>
                    <p className="summary-card-value">{monthsToYearsLabel(plan.months_to_debt_free)}</p>
                  </div>
                </div>
                <div className="card summary-card summary-card--expense">
                  <div>
                    <p className="summary-card-label">Total interest paid</p>
                    <p className="summary-card-value">{formatMoney(plan.total_interest)}</p>
                  </div>
                </div>
              </div>

              <div className="table-scroll" style={{ marginTop: "1rem" }}>
                <table className="transaction-list">
                  <thead>
                    <tr>
                      <th>Order</th>
                      <th>Debt</th>
                      <th>Paid off in</th>
                      <th>Interest paid</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plan.debts.map((d, i) => (
                      <tr key={d.id}>
                        <td>{i + 1}</td>
                        <td>{d.name}</td>
                        <td>{monthsToYearsLabel(d.payoff_month)}</td>
                        <td className="amount-cell expense">{formatMoney(d.total_interest)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default DebtPayoff;
