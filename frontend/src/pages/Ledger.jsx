import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import SummaryCard from "../components/SummaryCard";
import Select from "../components/Select";
import { IconEdit, IconPlus, IconTrash, IconTrendingDown, IconTrendingUp, IconUser } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import {
  createBook,
  createParty,
  deleteParty,
  getBooks,
  getPartiesSummary,
  updateParty,
} from "../services/api";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const EMPTY_PARTY_FORM = { name: "", type: "customer", phone: "", note: "" };
const EMPTY_BOOK_FORM = { name: "", type: "personal" };

const BOOK_TYPE_OPTIONS = [
  { value: "personal", label: "Personal" },
  { value: "business", label: "Business" },
  { value: "home", label: "Home" },
  { value: "daily", label: "Daily" },
];

function Ledger() {
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);

  const [books, setBooks] = useState([]);
  const [bookId, setBookId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [partyForm, setPartyForm] = useState(EMPTY_PARTY_FORM);
  const [editingPartyId, setEditingPartyId] = useState(null);

  const [showBookForm, setShowBookForm] = useState(false);
  const [bookForm, setBookForm] = useState(EMPTY_BOOK_FORM);

  function loadBooks() {
    return getBooks(token).then((data) => {
      setBooks(data);
      if (!bookId && data.length > 0) {
        const preferred = data.find((b) => b.is_default) || data[0];
        setBookId(preferred.id);
      }
      return data;
    });
  }

  function refreshSummary(id) {
    if (!id) return Promise.resolve();
    setLoading(true);
    return getPartiesSummary(token, { bookId: id })
      .then(setSummary)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadBooks().catch((err) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (bookId) refreshSummary(bookId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  function handleEditParty(party) {
    setEditingPartyId(party.id);
    setPartyForm({
      name: party.name,
      type: party.type,
      phone: party.phone || "",
      note: party.note || "",
    });
  }

  function handleCancelPartyEdit() {
    setEditingPartyId(null);
    setPartyForm(EMPTY_PARTY_FORM);
  }

  async function handlePartySubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      if (editingPartyId) {
        await updateParty(editingPartyId, partyForm, token);
        setEditingPartyId(null);
      } else {
        await createParty({ ...partyForm, book_id: bookId }, token);
      }
      setPartyForm(EMPTY_PARTY_FORM);
      await refreshSummary(bookId);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteParty(id) {
    setError(null);
    try {
      await deleteParty(id, token);
      if (editingPartyId === id) handleCancelPartyEdit();
      await refreshSummary(bookId);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCreateBook(event) {
    event.preventDefault();
    setError(null);
    try {
      const book = await createBook(bookForm, token);
      setBookForm(EMPTY_BOOK_FORM);
      setShowBookForm(false);
      const updated = await loadBooks();
      setBookId(book.book?.id ?? updated.find((b) => b.name === bookForm.name)?.id);
    } catch (err) {
      setError(err.message);
    }
  }

  const parties = summary?.parties || [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Ledger</h1>
        <p>Track who owes you and who you owe — a running account per customer or supplier.</p>
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
        <button type="button" className="btn-secondary" onClick={() => setShowBookForm((v) => !v)}>
          {showBookForm ? "Cancel" : "+ New book"}
        </button>
      </div>

      {showBookForm && (
        <form className="card card-padded transaction-form" onSubmit={handleCreateBook}>
          <div className="form-row">
            <label>
              Name
              <input
                type="text"
                value={bookForm.name}
                onChange={(e) => setBookForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. My Shop"
                required
              />
            </label>
            <label>
              Type
              <Select
                ariaLabel="Book type"
                value={bookForm.type}
                onChange={(type) => setBookForm((f) => ({ ...f, type }))}
                options={BOOK_TYPE_OPTIONS}
              />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit">
              <IconPlus width={16} height={16} />
              Create Book
            </button>
          </div>
        </form>
      )}

      {summary && (
        <div className="summary-grid">
          <SummaryCard
            label="You'll get"
            value={formatMoney(summary.you_will_get)}
            variant="income"
            icon={IconTrendingUp}
          />
          <SummaryCard
            label="You'll give"
            value={formatMoney(summary.you_will_give)}
            variant="expense"
            icon={IconTrendingDown}
          />
          <SummaryCard label="Net" value={formatMoney(summary.net)} variant="balance" icon={IconUser} />
        </div>
      )}

      <form className="card card-padded transaction-form" onSubmit={handlePartySubmit}>
        <div className="form-row">
          <label>
            Name
            <input
              type="text"
              value={partyForm.name}
              onChange={(e) => setPartyForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Ramesh Traders"
              required
            />
          </label>
          <label>
            Type
            <Select
              ariaLabel="Party type"
              value={partyForm.type}
              onChange={(type) => setPartyForm((f) => ({ ...f, type }))}
              disabled={Boolean(editingPartyId)}
              options={[
                { value: "customer", label: "Customer (owes you)" },
                { value: "supplier", label: "Supplier (you owe)" },
              ]}
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            Phone
            <input
              type="text"
              value={partyForm.phone}
              onChange={(e) => setPartyForm((f) => ({ ...f, phone: e.target.value }))}
              placeholder="Optional — needed to send WhatsApp/SMS reminders"
            />
          </label>
          <label>
            Note
            <input
              type="text"
              value={partyForm.note}
              onChange={(e) => setPartyForm((f) => ({ ...f, note: e.target.value }))}
              placeholder="Optional"
            />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            {editingPartyId ? "Save Changes" : "Add Party"}
          </button>
          {editingPartyId && (
            <button type="button" className="link-btn" onClick={handleCancelPartyEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {loading ? (
        <p className="loading-state">Loading ledger...</p>
      ) : parties.length === 0 ? (
        <div className="card empty-state">
          <IconUser width={36} height={36} />
          <p>No parties in this book yet — add a customer or supplier above.</p>
        </div>
      ) : (
        <div className="card transaction-list-card">
          <div className="table-scroll">
            <table className="transaction-list">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Phone</th>
                  <th>Balance</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {parties.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <Link to={`/ledger/${p.id}`} className="link-btn" style={{ fontWeight: 600 }}>
                        {p.name}
                      </Link>
                    </td>
                    <td style={{ textTransform: "capitalize" }}>{p.type}</td>
                    <td>{p.phone || "—"}</td>
                    <td
                      className={`amount-cell ${p.balance_direction === "you_will_get" ? "income" : p.balance_direction === "you_will_give" ? "expense" : ""}`}
                    >
                      {p.balance_direction === "settled" ? "Settled" : `${p.balance_label} ${formatMoney(p.balance_abs)}`}
                    </td>
                    <td className="row-actions">
                      <button
                        type="button"
                        className="btn-icon"
                        onClick={() => handleEditParty(p)}
                        aria-label={`Edit ${p.name}`}
                      >
                        <IconEdit width={16} height={16} />
                      </button>
                      <button
                        type="button"
                        className="btn-icon danger"
                        onClick={() => handleDeleteParty(p.id)}
                        aria-label={`Delete ${p.name}`}
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

export default Ledger;
