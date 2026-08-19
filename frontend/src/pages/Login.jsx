import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
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
    <div className="page page-narrow">
      <div className="card card-padded">
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
          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </label>
          <button type="submit">Login</button>
        </form>
        <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", marginTop: "1rem" }}>
          No account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
