import { IconCheck, IconTrendingDown, IconTrendingUp } from "./icons";
import { LogoMark } from "./Logo";

const FEATURES = [
  "Track every income & expense in seconds",
  "See spending trends with visual reports",
  "Set budgets and hit your savings goals",
  "Your data stays private and secure",
];

function AuthLayout({ children }) {
  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-visual-blob auth-visual-blob-1" />
        <div className="auth-visual-blob auth-visual-blob-2" />

        <div className="auth-visual-content">
          <div className="auth-visual-brand">
            <LogoMark size={30} tile={false} />
            Hisaab
          </div>

          <div className="auth-visual-copy">
            <h2>Master your money, one transaction at a time.</h2>
            <p>
              Track spending, hit savings goals, and see exactly where your money goes — all in
              one place.
            </p>
          </div>

          <div className="auth-mock-card">
            <div className="auth-mock-card-header">
              <span>This month</span>
              <span className="auth-mock-card-balance">$4,285.50</span>
            </div>
            <div className="auth-mock-card-row">
              <span className="auth-mock-pill income">
                <IconTrendingUp width={13} height={13} />
                Income
              </span>
              <span>$6,120.00</span>
            </div>
            <div className="auth-mock-card-row">
              <span className="auth-mock-pill expense">
                <IconTrendingDown width={13} height={13} />
                Expenses
              </span>
              <span>$1,834.50</span>
            </div>
            <div className="auth-mock-bars">
              {[40, 70, 55, 90, 35, 65, 50].map((h, i) => (
                <div key={i} className="auth-mock-bar" style={{ height: `${h}%` }} />
              ))}
            </div>
          </div>

          <ul className="auth-feature-list">
            {FEATURES.map((feature) => (
              <li key={feature}>
                <span className="auth-feature-icon">
                  <IconCheck width={13} height={13} />
                </span>
                {feature}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="auth-form-side">{children}</div>
    </div>
  );
}

export default AuthLayout;
