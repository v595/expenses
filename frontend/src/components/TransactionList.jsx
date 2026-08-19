// transactions is an array passed in as a prop. We render one row per item
// using .map(). Each row needs a unique `key` (transaction.id) so React can
// tell rows apart when the list changes (add/edit/delete) without re-rendering everything.
function TransactionList({ transactions, onEdit, onDelete }) {
  if (transactions.length === 0) {
    return <p className="empty-state">No transactions yet. Add one above.</p>;
  }

  return (
    <table className="transaction-list">
      <thead>
        <tr>
          <th>Date</th>
          <th>Category</th>
          <th>Description</th>
          <th>Type</th>
          <th>Amount</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {transactions.map((transaction) => (
          <tr key={transaction.id} className={`row-${transaction.type}`}>
            <td>{transaction.date}</td>
            <td>{transaction.category}</td>
            <td>{transaction.description}</td>
            <td>{transaction.type}</td>
            <td>{transaction.type === "expense" ? "-" : "+"}{transaction.amount}</td>
            <td>
              <button onClick={() => onEdit(transaction)}>Edit</button>
              <button onClick={() => onDelete(transaction.id)}>Delete</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default TransactionList;
