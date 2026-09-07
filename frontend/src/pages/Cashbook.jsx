import { useEffect, useRef, useState } from "react";

import DatePicker from "../components/DatePicker";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import { getBooks, getCashbook } from "../services/api";
import { formatMoney as formatMoneyIn } from "../utils/currency";

function Cashbook() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);

  const [books, setBooks] = useState([]);
  const [bookId, setBookId] = useState(null);
  const [range, setRange] = useState({ start_date: "", end_date: "" });
  const [cashbook, setCashbook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const toDateRef = useRef(null);

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

  function refresh() {
    if (!bookId) return;
    setLoading(true);
    getCashbook(token, { bookId, ...range })
      .then(setCashbook)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Cashbook</h1>
        <p>A day-by-day view of every ledger entry in a book, with a running balance.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="form-row" style={{ alignItems: "flex-end" }}>
        <label style={{ maxWidth: 260 }}>
          Book
          <Select
            ariaLabel="Book"
            value={bookId ?? ""}
            onChange={(value) => setBookId(Number(value))}
            options={books.map((b) => ({ value: b.id, label: `${b.name}${b.is_default ? " (default)" : ""}` }))}
          />
        </label>
        <label>
          From
          <DatePicker
            ariaLabel="From date"
            value={range.start_date}
            onChange={(date) => {
              setRange((r) => ({ ...r, start_date: date }));
              toDateRef.current?.open();
            }}
          />
        </label>
        <label>
          To
          <DatePicker
            ref={toDateRef}
            ariaLabel="To date"
            value={range.end_date}
            onChange={(date) => setRange((r) => ({ ...r, end_date: date }))}
          />
        </label>
        <button type="button" className="btn-secondary" onClick={refresh}>
          Apply
        </button>
      </div>

      {loading ? (
        <p className="loading-state">Loading cashbook...</p>
      ) : !cashbook || cashbook.days.length === 0 ? (
        <div className="card empty-state">
          <p>No ledger activity in this window.</p>
        </div>
      ) : (
        <>
          <div className="summary-grid">
            <div className="card summary-card summary-card--balance">
              <div>
                <p className="summary-card-label">Opening balance</p>
                <p className="summary-card-value">{formatMoney(cashbook.opening_balance)}</p>
              </div>
            </div>
            <div className="card summary-card summary-card--income">
              <div>
                <p className="summary-card-label">Total given</p>
                <p className="summary-card-value">{formatMoney(cashbook.total_given)}</p>
              </div>
            </div>
            <div className="card summary-card summary-card--expense">
              <div>
                <p className="summary-card-label">Total got</p>
                <p className="summary-card-value">{formatMoney(cashbook.total_got)}</p>
              </div>
            </div>
            <div className="card summary-card summary-card--balance">
              <div>
                <p className="summary-card-label">Closing balance</p>
                <p className="summary-card-value">{formatMoney(cashbook.closing_balance)}</p>
              </div>
            </div>
          </div>

          {cashbook.days.map((day) => (
            <div className="card transaction-list-card" key={day.date} style={{ marginBottom: "1rem" }}>
              <div
                className="card-padded"
                style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}
              >
                <strong>{day.date}</strong>
                <span>
                  Opening {formatMoney(day.opening_balance)} → Closing {formatMoney(day.closing_balance)}
                </span>
              </div>
              <div className="table-scroll">
                <table className="transaction-list">
                  <thead>
                    <tr>
                      <th>Party</th>
                      <th>Description</th>
                      <th>You Gave</th>
                      <th>You Got</th>
                    </tr>
                  </thead>
                  <tbody>
                    {day.entries.map((e) => (
                      <tr key={e.id}>
                        <td style={{ textTransform: "capitalize" }}>{e.party_name}</td>
                        <td>{e.description || "—"}</td>
                        <td className="amount-cell expense">{e.direction === "given" ? formatMoney(e.amount) : ""}</td>
                        <td className="amount-cell income">{e.direction === "got" ? formatMoney(e.amount) : ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

export default Cashbook;
