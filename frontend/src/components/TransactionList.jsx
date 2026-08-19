import { IconEdit, IconReceipt, IconTrash } from "./icons";
import { categoryColor } from "../utils/categoryColor";

function TransactionList({ transactions, onEdit, onDelete }) {
  if (transactions.length === 0) {
    return (
      <div className="card transaction-list-card empty-state">
        <IconReceipt width={36} height={36} />
        <p>No transactions match your filters. Try adding one above.</p>
      </div>
    );
  }

  return (
    <div className="card transaction-list-card">
      <div className="table-scroll">
        <table className="transaction-list">
          <thead>
            <tr>
              <th>Date</th>
              <th>Category</th>
              <th>Description</th>
              <th>Amount</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((transaction) => (
              <tr key={transaction.id}>
                <td>{transaction.date}</td>
                <td>
                  <span className="category-badge">
                    <span
                      className="category-dot"
                      style={{ background: categoryColor(transaction.category) }}
                    />
                    {transaction.category}
                  </span>
                </td>
                <td>{transaction.description || "—"}</td>
                <td className={`amount-cell ${transaction.type}`}>
                  {transaction.type === "expense" ? "-" : "+"}
                  {transaction.amount}
                </td>
                <td>
                  <div className="row-actions">
                    <button className="btn-icon" title="Edit" onClick={() => onEdit(transaction)}>
                      <IconEdit width={16} height={16} />
                    </button>
                    <button
                      className="btn-icon danger"
                      title="Delete"
                      onClick={() => onDelete(transaction.id)}
                    >
                      <IconTrash width={16} height={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TransactionList;
