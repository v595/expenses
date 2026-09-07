import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { IconEdit, IconPlus, IconTrash } from "../components/icons";
import DatePicker from "../components/DatePicker";
import Select from "../components/Select";
import { useAuth } from "../context/AuthContext";
import {
  createLedgerEntry,
  createReminder,
  deleteLedgerEntry,
  getParty,
  getPartyStatement,
  getReminders,
  markReminderSent,
  updateLedgerEntry,
} from "../services/api";
import { fromBase, toBase } from "../utils/fx";
import { formatMoney as formatMoneyIn } from "../utils/currency";

const EMPTY_FORM = {
  direction: "given",
  amount: "",
  description: "",
  date: new Date().toISOString().slice(0, 10),
  due_date: "",
};

function PartyDetail() {
  const { partyId } = useParams();
  const { token, user } = useAuth();
  const formatMoney = (amount) => formatMoneyIn(amount, user.currency);

  const [party, setParty] = useState(null);
  const [statement, setStatement] = useState(null);
  const [reminders, setReminders] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sendingReminder, setSendingReminder] = useState(false);

  function refresh() {
    setLoading(true);
    return Promise.all([
      getParty(partyId, token),
      getPartyStatement(partyId, token),
      getReminders(token, { partyId }),
    ])
      .then(([p, s, r]) => {
        setParty(p);
        setStatement(s);
        setReminders(r);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [partyId, token]);

  function handleEdit(entry) {
    setEditingId(entry.id);
    setForm({
      direction: entry.direction,
      amount: fromBase(entry.amount, user.currency),
      description: entry.description || "",
      date: entry.date,
      due_date: entry.due_date || "",
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
        ...form,
        amount: toBase(form.amount, user.currency),
        due_date: form.due_date || null,
        party_id: Number(partyId),
      };
      if (editingId) {
        await updateLedgerEntry(editingId, payload, token);
        setEditingId(null);
      } else {
        await createLedgerEntry(payload, token);
      }
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteLedgerEntry(id, token);
      if (editingId === id) handleCancelEdit();
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSendReminder(channel) {
    setError(null);
    setNotice(null);
    setSendingReminder(true);
    try {
      const result = await createReminder({ party_id: Number(partyId), channel }, token);
      if (result.link) {
        window.open(result.link, "_blank", "noopener,noreferrer");
        setNotice("Reminder link opened — send it, then mark it as sent below.");
      } else {
        setNotice("Reminder recorded.");
      }
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setSendingReminder(false);
    }
  }

  async function handleMarkSent(id) {
    setError(null);
    try {
      await markReminderSent(id, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading && !party) {
    return (
      <div className="page">
        <p className="loading-state">Loading...</p>
      </div>
    );
  }

  if (!party) return null;

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/ledger" className="link-btn">
          ← Back to Ledger
        </Link>
        <h1 style={{ marginTop: "0.4rem" }}>{party.name}</h1>
        <p style={{ textTransform: "capitalize" }}>
          {party.type} {party.phone ? `· ${party.phone}` : ""}
        </p>
      </div>

      {error && <p className="error-message">{error}</p>}
      {notice && <p className="success-message">{notice}</p>}

      <div className="card card-padded" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
        <div>
          <p style={{ color: "var(--color-text-muted)", fontSize: "0.85rem", margin: 0 }}>
            {party.balance_direction === "settled" ? "Balance" : party.balance_label}
          </p>
          <p
            className={`amount-cell ${party.balance_direction === "you_will_get" ? "income" : party.balance_direction === "you_will_give" ? "expense" : ""}`}
            style={{ fontSize: "1.5rem", fontWeight: 700 }}
          >
            {formatMoney(party.balance_abs)}
          </p>
        </div>
        <div className="form-actions" style={{ margin: 0 }}>
          <button type="button" className="btn-secondary" disabled={sendingReminder} onClick={() => handleSendReminder("whatsapp")}>
            Remind via WhatsApp
          </button>
          <button type="button" className="btn-secondary" disabled={sendingReminder} onClick={() => handleSendReminder("inapp")}>
            Log reminder (in-app)
          </button>
        </div>
      </div>

      <form className="card card-padded transaction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Type
            <Select
              ariaLabel="Entry direction"
              value={form.direction}
              onChange={(direction) => setForm((f) => ({ ...f, direction }))}
              options={[
                { value: "given", label: "You Gave" },
                { value: "got", label: "You Got" },
              ]}
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
            Date
            <DatePicker
              ariaLabel="Entry date"
              value={form.date}
              onChange={(date) => setForm((f) => ({ ...f, date }))}
            />
          </label>
          <label>
            Due Date
            <DatePicker
              ariaLabel="Due date"
              placeholder="Optional"
              value={form.due_date}
              onChange={(date) => setForm((f) => ({ ...f, due_date: date }))}
            />
          </label>
        </div>
        <label>
          Description
          <input
            type="text"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            placeholder="Optional"
          />
        </label>
        <div className="form-actions">
          <button type="submit">
            <IconPlus width={16} height={16} />
            {editingId ? "Save Changes" : "Add Entry"}
          </button>
          {editingId && (
            <button type="button" className="link-btn" onClick={handleCancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {statement && statement.entries.length === 0 ? (
        <div className="card empty-state">
          <p>No entries yet — add one above.</p>
        </div>
      ) : (
        statement && (
          <div className="card transaction-list-card">
            <div className="table-scroll">
              <table className="transaction-list">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>You Gave</th>
                    <th>You Got</th>
                    <th>Balance</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {statement.entries.map((e) => (
                    <tr key={e.id}>
                      <td>{e.date}</td>
                      <td>{e.description || "—"}</td>
                      <td className="amount-cell expense">{e.direction === "given" ? formatMoney(e.amount) : ""}</td>
                      <td className="amount-cell income">{e.direction === "got" ? formatMoney(e.amount) : ""}</td>
                      <td>{formatMoney(e.running_balance)}</td>
                      <td className="row-actions">
                        <button
                          type="button"
                          className="btn-icon"
                          onClick={() => handleEdit(e)}
                          aria-label="Edit entry"
                        >
                          <IconEdit width={16} height={16} />
                        </button>
                        <button
                          type="button"
                          className="btn-icon danger"
                          onClick={() => handleDelete(e.id)}
                          aria-label="Delete entry"
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
        )
      )}

      {reminders.length > 0 && (
        <div className="card card-padded">
          <h2 className="card-title">Reminder history</h2>
          <div className="table-scroll">
            <table className="transaction-list">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Channel</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {reminders.map((r) => (
                  <tr key={r.id}>
                    <td>{r.created_at}</td>
                    <td style={{ textTransform: "capitalize" }}>{r.channel}</td>
                    <td style={{ textTransform: "capitalize" }}>{r.status}</td>
                    <td className="row-actions">
                      {r.status === "pending" && (
                        <button type="button" className="btn-secondary" onClick={() => handleMarkSent(r.id)}>
                          Mark sent
                        </button>
                      )}
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

export default PartyDetail;
