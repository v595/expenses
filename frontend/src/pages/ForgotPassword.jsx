import { useState } from "react";
import { Link } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import { requestPasswordReset } from "../services/api";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState(null);
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await requestPasswordReset(email);
      // Same confirmation regardless of whether the email is registered —
      // matches the backend, which never reveals that either.
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="card card-padded auth-card">
        <div className="page-header">
          <h1>Reset your password</h1>
          <p>Enter your account email and we'll send you a reset link.</p>
        </div>
        {error && <p className="error-message">{error}</p>}
        {sent ? (
          <p className="social-auth-notice">
            If that email has an account, a reset link is on its way — check your inbox.
          </p>
        ) : (
          <form onSubmit={handleSubmit}>
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                required
              />
            </label>
            <button type="submit" disabled={submitting}>
              {submitting ? "Sending..." : "Send reset link"}
            </button>
          </form>
        )}
        <p className="auth-footer-text">
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </AuthLayout>
  );
}

export default ForgotPassword;
