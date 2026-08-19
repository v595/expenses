import { useEffect, useState } from "react";

import { IconSearch } from "../components/icons";
import TransactionForm from "../components/TransactionForm";
import TransactionList from "../components/TransactionList";
import { useAuth } from "../context/AuthContext";
import {
  createTransaction,
  deleteTransaction,
  getTransactions,
  updateTransaction,
} from "../services/api";

const EMPTY_FILTERS = { search: "", category: "", type: "", start_date: "", end_date: "" };

function Transactions() {
  const { token } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [editingTransaction, setEditingTransaction] = useState(null); // null = "add" mode
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="page">
      <div className="page-header">
        <h1>Transactions</h1>
        <p>Add, edit, and filter your income and expenses.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      <TransactionForm
        key={editingTransaction ? editingTransaction.id : "new"}
        initialValues={editingTransaction}
        onSubmit={editingTransaction ? handleUpdate : handleAdd}
        onCancel={editingTransaction ? () => setEditingTransaction(null) : null}
      />

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
          <select name="type" value={filters.type} onChange={handleFilterChange}>
            <option value="">All types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </div>
        <div className="filter-field">
          <label>From</label>
          <input type="date" name="start_date" value={filters.start_date} onChange={handleFilterChange} />
        </div>
        <div className="filter-field">
          <label>To</label>
          <input type="date" name="end_date" value={filters.end_date} onChange={handleFilterChange} />
        </div>
        <button type="button" className="btn-secondary" onClick={() => setFilters(EMPTY_FILTERS)}>
          Clear
        </button>
      </div>

      {loading ? (
        <p className="loading-state">Loading transactions...</p>
      ) : (
        <TransactionList
          transactions={transactions}
          onEdit={setEditingTransaction}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}

export default Transactions;
