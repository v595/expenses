import { useEffect, useState } from "react";

import Select from "./Select";
import { useAuth } from "../context/AuthContext";
import { createLedgerEntry, getBooks, getParties } from "../services/api";
import { toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

// Splits an existing expense transaction's cost with other people, by
// recording a ledger "given" entry against each selected party for their
// share — the same running-balance ledger the Ledger/Cashbook pages read.
function SplitExpenseForm({ transaction, onClose, onDone }) {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);

  const [books, setBooks] = useState([]);
  const [bookId, setBookId] = useState(null);
  const [parties, setParties] = useState([]);
  const [selected, setSelected] = useState({}); // partyId -> true
  const [mode, setMode] = useState("equal"); // "equal" | "custom"
  const [customAmounts, setCustomAmounts] = useState({}); // partyId -> string
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getBooks(token)
      .then((data) => {
        setBooks(data);
        const preferred = data.find((b) => b.is_default) || data[0];
        if (preferred) setBookId(preferred.id);
      })
      .catch((err) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (!bookId) return;
    getParties(token, { bookId, type: "customer" })
      .then(setParties)
      .catch((err) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  const selectedIds = Object.keys(selected).filter((id) => selected[id]);
  const totalAmountBase = transaction.amount; // already base currency
  const shareCountIncludingYou = selectedIds.length + 1;
  const equalShareBase = selectedIds.length > 0 ? totalAmountBase / shareCountIncludingYou : 0;

  function toggleParty(id) {
    setSelected((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    if (selectedIds.length === 0) {
      setError("Select at least one person to split with.");
      return;
    }

    let shares; // { partyId: amountBase }
    if (mode === "equal") {
      shares = Object.fromEntries(selectedIds.map((id) => [id, equalShareBase]));
    } else {
      shares = {};
      let assigned = 0;
      for (const id of selectedIds) {
        const amount = toBase(customAmounts[id] || 0, user.currency);
        if (!amount || amount <= 0) {
          setError("Enter a share amount for every selected person.");
          return;
        }
        shares[id] = amount;
        assigned += amount;
      }
      if (assigned >= totalAmountBase) {
        setError("The split shares can't add up to the full amount or more — leave some for yourself.");
        return;
      }
    }

    setSaving(true);
    try {
      const description = `Split: ${transaction.description || transaction.category}`;
      for (const id of selectedIds) {
        await createLedgerEntry(
          {
            party_id: Number(id),
            book_id: bookId,
            amount: Math.round(shares[id] * 100) / 100,
            direction: "given",
            description,
            date: transaction.date,
          },
          token
        );
      }
      onDone?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
      <div className="profile-card-head">
        <h2 className="card-title">
          Split "{transaction.description || transaction.category}" ({formatMoney(transaction.amount)})
        </h2>
        <p>Records what each person owes you as a ledger entry against them.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      {parties.length === 0 ? (
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.88rem" }}>
          No customers in your default book yet — add one on the Ledger page first.
        </p>
      ) : (
        <>
          <label>Split with</label>
          <div className="category-chip-list">
            {parties.map((p) => (
              <label
                key={p.id}
                className="category-chip"
                style={{ cursor: "pointer", background: selected[p.id] ? "var(--color-primary-soft)" : undefined }}
              >
                <input
                  type="checkbox"
                  checked={Boolean(selected[p.id])}
                  onChange={() => toggleParty(p.id)}
                  style={{ margin: 0 }}
                />
                {p.name}
              </label>
            ))}
          </div>

          {selectedIds.length > 0 && (
            <>
              <div className="form-row">
                <label>
                  Split mode
                  <Select
                    ariaLabel="Split mode"
                    value={mode}
                    onChange={setMode}
                    options={[
                      { value: "equal", label: "Equal shares" },
                      { value: "custom", label: "Custom amounts" },
                    ]}
                  />
                </label>
              </div>

              {mode === "equal" ? (
                <p style={{ fontSize: "0.88rem" }}>
                  Each of the {shareCountIncludingYou} people (including you) pays {formatMoney(equalShareBase)}.
                </p>
              ) : (
                selectedIds.map((id) => {
                  const party = parties.find((p) => String(p.id) === id);
                  return (
                    <label key={id}>
                      {party?.name}'s share
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={customAmounts[id] || ""}
                        onChange={(e) => setCustomAmounts((prev) => ({ ...prev, [id]: e.target.value }))}
                        required
                      />
                    </label>
                  );
                })
              )}
            </>
          )}
        </>
      )}

      <div className="form-actions">
        <button type="submit" disabled={saving || parties.length === 0}>
          {saving ? "Saving..." : "Record Split"}
        </button>
        <button type="button" className="link-btn" onClick={onClose}>
          Cancel
        </button>
      </div>
    </form>
  );
}

export default SplitExpenseForm;
