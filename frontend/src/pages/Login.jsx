import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import PasswordField from "../components/PasswordField";
import SocialAuthButtons from "../components/SocialAuthButtons";
import { useAuth } from "../context/AuthContext";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
  // Set once the server says the password checked out but this account has
  // 2FA on — the form below swaps to a code-entry step for this ticket.
  const [twoFactorTicket, setTwoFactorTicket] = useState(null);
  const [code, setCode] = useState("");
  const { login, verifyTwoFactor } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const justResetPassword = Boolean(location.state?.passwordReset);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      const result = await login(form.email, form.password);
      if (result.requires_two_factor) {
        setTwoFactorTicket(result.ticket);
        return;
      }
      navigate("/transactions");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleVerifyCode(event) {
    event.preventDefault();
    setError(null);
    try {
      await verifyTwoFactor(twoFactorTicket, code);
      navigate("/transactions");
    } catch (err) {
      setError(err.message);
    }
  }

  if (twoFactorTicket) {
    return (
      <AuthLayout>
        <div className="card card-padded auth-card">
          <div className="page-header">
            <h1>Two-factor code</h1>
            <p>Enter the 6-digit code from your authenticator app.</p>
          </div>
          {error && <p className="error-message">{error}</p>}
          <form onSubmit={handleVerifyCode}>
            <label>
              Code
              <input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                maxLength={6}
                autoFocus
                required
              />
            </label>
            <button type="submit">Verify</button>
          </form>
          <button type="button" className="link-btn" onClick={() => setTwoFactorTicket(null)}>
            Back to login
          </button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="card card-padded auth-card">
        <div className="page-header">
          <h1>Welcome back</h1>
          <p>Log in to your account.</p>
        </div>
        {justResetPassword && (
          <p className="social-auth-notice">Password reset — log in with your new password.</p>
        )}
        {error && <p className="error-message">{error}</p>}
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </label>
          <PasswordField
            label="Password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
          />
          <Link to="/forgot-password" className="link-btn">
            Forgot password?
          </Link>
          <button type="submit">Login</button>
        </form>
        <SocialAuthButtons onRequiresTwoFactor={setTwoFactorTicket} />
        <p className="auth-footer-text">
          No account? <Link to="/register">Register</Link>
        </p>
      </div>
    </AuthLayout>
  );
}

export default Login;
