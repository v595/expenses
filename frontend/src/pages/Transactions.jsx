import { useEffect, useState } from "react";

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
      <h1>Transactions</h1>
      {error && <p className="error-message">{error}</p>}

      <TransactionForm
        key={editingTransaction ? editingTransaction.id : "new"}
        initialValues={editingTransaction}
        onSubmit={editingTransaction ? handleUpdate : handleAdd}
        onCancel={editingTransaction ? () => setEditingTransaction(null) : null}
      />

      <div className="filter-bar">
        <input
          type="text"
          name="search"
          placeholder="Search description/category"
          value={filters.search}
          onChange={handleFilterChange}
        />
        <input
          type="text"
          name="category"
          placeholder="Category"
          value={filters.category}
          onChange={handleFilterChange}
        />
        <select name="type" value={filters.type} onChange={handleFilterChange}>
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <input type="date" name="start_date" value={filters.start_date} onChange={handleFilterChange} />
        <input type="date" name="end_date" value={filters.end_date} onChange={handleFilterChange} />
        <button type="button" onClick={() => setFilters(EMPTY_FILTERS)}>
          Clear
        </button>
      </div>

      {loading ? (
        <p>Loading...</p>
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
