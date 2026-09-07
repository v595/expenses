import { useEffect, useRef, useState } from "react";

import { IconDownload, IconSearch, IconUpload } from "../components/icons";
import Select from "../components/Select";
import SplitExpenseForm from "../components/SplitExpenseForm";
import TransactionForm from "../components/TransactionForm";
import TransactionList from "../components/TransactionList";
import { useAuth } from "../context/AuthContext";
import {
  createTransaction,
  deleteTransaction,
  getTags,
  getTransactions,
  importTransactions,
  updateTransaction,
} from "../services/api";
import { downloadTransactionsCsv } from "../utils/downloadCsv";
import { parseSmsText } from "../utils/parseSms";
import { parseTransactionsCsv } from "../utils/parseTransactionsCsv";

const EMPTY_FILTERS = { search: "", category: "", type: "", start_date: "", end_date: "", tag_id: "" };

function Transactions() {
  const { token } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [tags, setTags] = useState([]);
  const [editingTransaction, setEditingTransaction] = useState(null); // null = "add" mode
  const [splittingTransaction, setSplittingTransaction] = useState(null);
  const [splitNotice, setSplitNotice] = useState(null);
  const [showSmsPaste, setShowSmsPaste] = useState(false);
  const [smsText, setSmsText] = useState("");
  const [smsPrefill, setSmsPrefill] = useState(null);
  const [smsError, setSmsError] = useState(null);
  const [formKey, setFormKey] = useState(0);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [importSummary, setImportSummary] = useState(null);
  const fileInputRef = useRef(null);

  function refresh() {
    setLoading(true);
    return getTransactions(token, filters)
      .then(setTransactions)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  // Re-fetches whenever a filter changes, so the list always reflects the
  // currently active filters (including right after an add/edit/delete).
  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, filters]);

  useEffect(() => {
    getTags(token).then(setTags).catch(() => {});
  }, [token]);

  function handleFilterChange(event) {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  }

  async function handleAdd(data) {
    setError(null);
    try {
      await createTransaction(data, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpdate(data) {
    setError(null);
    try {
      await updateTransaction(editingTransaction.id, data, token);
      setEditingTransaction(null);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteTransaction(id, token);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  function handleParseSms() {
    setSmsError(null);
    const parsed = parseSmsText(smsText);
    if (!parsed) {
      setSmsError("Couldn't find an amount in that text — paste the full SMS.");
      return;
    }
    setSmsPrefill({
      amount: String(parsed.amount),
      type: parsed.type || "expense",
      date: parsed.date || new Date().toISOString().slice(0, 10),
      description: parsed.description || "",
    });
    setEditingTransaction(null);
    setSplittingTransaction(null);
    setFormKey((k) => k + 1);
    setShowSmsPaste(false);
    setSmsText("");
  }

  async function handleImportFile(event) {
    const file = event.target.files[0];
    event.target.value = "";
    if (!file) return;

    setError(null);
    setImportSummary(null);
    setImporting(true);
    try {
      const text = await file.text();
      const rows = parseTransactionsCsv(text);
      const result = await importTransactions(rows, token);
      setImportSummary(result);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Transactions</h1>
        <p>Add, edit, and filter your income and expenses.</p>
      </div>

      {error && <p className="error-message">{error}</p>}
      {importSummary && (
        <p className={importSummary.errors.length > 0 ? "error-message" : "success-message"}>
          Imported {importSummary.imported} transaction{importSummary.imported === 1 ? "" : "s"}.
          {importSummary.errors.length > 0 &&
            ` ${importSummary.errors.length} row(s) skipped: ${importSummary.errors
              .map((e) => `row ${e.row} (${e.error})`)
              .join(", ")}`}
        </p>
      )}

      {splitNotice && <p className="success-message">{splitNotice}</p>}

      <div className="form-actions" style={{ marginBottom: "0.75rem" }}>
        <button type="button" className="btn-secondary" onClick={() => setShowSmsPaste((v) => !v)}>
          {showSmsPaste ? "Cancel" : "Paste Bank SMS"}
        </button>
      </div>

      {showSmsPaste && (
        <div className="card card-padded" style={{ marginBottom: "1rem" }}>
          <p style={{ marginTop: 0, fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
            Paste a bank debit/credit SMS — the amount, date, and merchant get pulled out and pre-filled
            below for you to review before saving. Nothing is created automatically.
          </p>
          {smsError && <p className="error-message">{smsError}</p>}
          <textarea
            rows={3}
            value={smsText}
            onChange={(e) => setSmsText(e.target.value)}
            placeholder="e.g. Rs.500.00 debited from A/c XX1234 on 07-09-26 to VPA merchant@ok. Avl Bal Rs 4500.00"
            style={{ width: "100%" }}
          />
          <div className="form-actions">
            <button type="button" onClick={handleParseSms} disabled={!smsText.trim()}>
              Parse
            </button>
          </div>
        </div>
      )}

      {splittingTransaction ? (
        <SplitExpenseForm
          transaction={splittingTransaction}
          onClose={() => setSplittingTransaction(null)}
          onDone={() => {
            setSplittingTransaction(null);
            setSplitNotice("Split recorded on the Ledger page.");
          }}
        />
      ) : (
        <TransactionForm
          key={editingTransaction ? `edit-${editingTransaction.id}` : `new-${formKey}`}
          initialValues={editingTransaction}
          prefillValues={editingTransaction ? undefined : smsPrefill}
          onSubmit={editingTransaction ? handleUpdate : handleAdd}
          onCancel={editingTransaction ? () => setEditingTransaction(null) : null}
        />
      )}

      <div className="card filter-bar">
        <div className="filter-field" style={{ flex: 1.4 }}>
          <label>Search</label>
          <div className="search-input-wrap">
            <IconSearch width={16} height={16} />
            <input
              type="text"
              name="search"
              placeholder="Description or category"
              value={filters.search}
              onChange={handleFilterChange}
            />
          </div>
        </div>
        <div className="filter-field">
          <label>Category</label>
          <input
            type="text"
            name="category"
            placeholder="e.g. Food"
            value={filters.category}
            onChange={handleFilterChange}
          />
        </div>
        <div className="filter-field">
          <label>Type</label>
          <Select
            ariaLabel="Filter by type"
            value={filters.type}
            onChange={(value) => handleFilterChange({ target: { name: "type", value } })}
            options={[
              { value: "", label: "All types" },
              { value: "income", label: "Income" },
              { value: "expense", label: "Expense" },
            ]}
          />
        </div>
        <div className="filter-field">
          <label>From</label>
          <input type="date" name="start_date" value={filters.start_date} onChange={handleFilterChange} />
        </div>
        <div className="filter-field">
          <label>To</label>
          <input type="date" name="end_date" value={filters.end_date} onChange={handleFilterChange} />
        </div>
        {tags.length > 0 && (
          <div className="filter-field">
            <label>Tag</label>
            <Select
              ariaLabel="Filter by tag"
              value={filters.tag_id}
              onChange={(value) => handleFilterChange({ target: { name: "tag_id", value } })}
              options={[
                { value: "", label: "All tags" },
                ...tags.map((t) => ({ value: String(t.id), label: t.name })),
              ]}
            />
          </div>
        )}
        <button type="button" className="btn-secondary" onClick={() => setFilters(EMPTY_FILTERS)}>
          Clear
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={handleImportFile}
          style={{ display: "none" }}
        />
        <button
          type="button"
          className="btn-secondary"
          onClick={() => fileInputRef.current.click()}
          disabled={importing}
        >
          <IconUpload width={16} height={16} />
          {importing ? "Importing..." : "Import CSV"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => downloadTransactionsCsv(transactions)}
          disabled={transactions.length === 0}
        >
          <IconDownload width={16} height={16} />
          Export CSV
        </button>
      </div>

      {loading ? (
        <p className="loading-state">Loading transactions...</p>
      ) : (
        <TransactionList
          transactions={transactions}
          onEdit={setEditingTransaction}
          onDelete={handleDelete}
          onSplit={setSplittingTransaction}
        />
      )}
    </div>
  );
}

export default Transactions;
