function SummaryCard({ label, value, variant, icon: Icon }) {
  return (
    <div className={`card summary-card summary-card--${variant}`}>
      <div className="summary-card-icon">
        <Icon width={20} height={20} />
      </div>
      <div>
        <p className="summary-card-label">{label}</p>
        <p className="summary-card-value">{value}</p>
      </div>
    </div>
  );
}

export default SummaryCard;
