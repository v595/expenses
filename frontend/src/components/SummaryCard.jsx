// props: data passed IN from the parent (Dashboard). This component never
// changes its own data — it just displays whatever it's given.
function SummaryCard({ label, value, variant }) {
  return (
    <div className={`summary-card summary-card--${variant}`}>
      <p className="summary-card-label">{label}</p>
      <p className="summary-card-value">{value}</p>
    </div>
  );
}

export default SummaryCard;
