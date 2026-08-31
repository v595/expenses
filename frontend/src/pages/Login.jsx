import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import PasswordField from "../components/PasswordField";
import SocialAuthButtons from "../components/SocialAuthButtons";
import { useAuth } from "../context/AuthContext";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
  const [forgotNotice, setForgotNotice] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      await login(form.email, form.password);
      navigate("/transactions");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <AuthLayout>
      <div className="card card-padded auth-card">
        <div className="page-header">
          <h1>Welcome back</h1>
          <p>Log in to your account.</p>
        </div>
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
          <button type="button" className="link-btn" onClick={() => setForgotNotice(true)}>
            Forgot password?
          </button>
          {forgotNotice && (
            <p className="social-auth-notice">Password reset isn't available yet.</p>
          )}
          <button type="submit">Login</button>
        </form>
        <SocialAuthButtons />
        <p className="auth-footer-text">
          No account? <Link to="/register">Register</Link>
        </p>
      </div>
    </AuthLayout>
  );
}

export default Login;
