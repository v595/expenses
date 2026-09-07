import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import PasswordField from "../components/PasswordField";
import { resetPassword } from "../services/api";

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords don't match");
      return;
    }
    setSubmitting(true);
    try {
      await resetPassword(token, password);
      navigate("/login", { state: { passwordReset: true } });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <AuthLayout>
        <div className="card card-padded auth-card">
          <div className="page-header">
            <h1>Reset your password</h1>
          </div>
          <p className="error-message">
            This link is missing its reset code. Request a new one from the login page.
          </p>
          <p className="auth-footer-text">
            <Link to="/forgot-password">Request a new link</Link>
          </p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="card card-padded auth-card">
        <div className="page-header">
          <h1>Choose a new password</h1>
        </div>
        {error && <p className="error-message">{error}</p>}
        <form onSubmit={handleSubmit}>
          <PasswordField
            label="New password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            required
          />
          <PasswordField
            label="Confirm password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Reset password"}
          </button>
        </form>
        <p className="auth-footer-text">
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </AuthLayout>
  );
}

export default ResetPassword;
