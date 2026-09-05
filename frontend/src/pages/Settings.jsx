import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { deleteAccountPermanently } from "../services/api";
import Select from "../components/Select";
import { FLAGS } from "../components/flags";
import { CURRENCIES } from "../utils/currency";

function Settings() {
  const { user, token, updateSettings, logout } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    currency: user.currency,
    notify_budget_alerts: user.notify_budget_alerts,
    notify_bill_reminders: user.notify_bill_reminders,
  });
  const [status, setStatus] = useState(null);
  const [saving, setSaving] = useState(false);

  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const [deleting, setDeleting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus(null);
    setSaving(true);
    try {
      await updateSettings(form);
      setStatus({ type: "success", message: "Settings saved." });
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteAccount() {
    setDeleteError(null);
    setDeleting(true);
    try {
      await deleteAccountPermanently(token);
      await logout();
      navigate("/login");
    } catch (err) {
      setDeleteError(err.message);
      setDeleting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Currency, notifications, and account-level controls.</p>
      </div>

      {status && (
        <p className={status.type === "error" ? "error-message" : "success-message"}>{status.message}</p>
      )}

      <form className="card card-padded" onSubmit={handleSubmit} style={{ marginBottom: "1.5rem" }}>
        <h2 className="card-title">Preferences</h2>

        <label>
          Currency
          <Select
            ariaLabel="Currency"
            value={form.currency}
            onChange={(currency) => setForm((f) => ({ ...f, currency }))}
            options={CURRENCIES.map((c) => ({
              value: c.code,
              label: `${c.label} (${c.symbol})`,
              hint: c.code,
              icon: FLAGS[c.code],
            }))}
          />
        </label>

        <div className="settings-toggle-row">
          <div>
            <div className="settings-toggle-label">Budget alerts</div>
            <div className="settings-toggle-hint">Notify me when I go over a category's monthly limit.</div>
          </div>
          <input
            type="checkbox"
            checked={form.notify_budget_alerts}
            onChange={(e) => setForm((f) => ({ ...f, notify_budget_alerts: e.target.checked }))}
          />
        </div>

        <div className="settings-toggle-row">
          <div>
            <div className="settings-toggle-label">Bill reminders</div>
            <div className="settings-toggle-hint">Notify me about bills due within 3 days.</div>
          </div>
          <input
            type="checkbox"
            checked={form.notify_bill_reminders}
            onChange={(e) => setForm((f) => ({ ...f, notify_bill_reminders: e.target.checked }))}
          />
        </div>

        <div className="form-actions">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </form>

      <div className="card card-padded danger-zone">
        <h2 className="card-title">Danger Zone</h2>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.88rem", marginTop: 0 }}>
          Permanently delete your account and every transaction, budget, and setting attached to it.
          This can't be undone.
        </p>
        {deleteError && <p className="error-message">{deleteError}</p>}
        {confirmingDelete ? (
          <div className="form-actions">
            <button type="button" className="btn-danger" onClick={handleDeleteAccount} disabled={deleting}>
              {deleting ? "Deleting..." : "Yes, delete everything"}
            </button>
            <button type="button" className="btn-secondary" onClick={() => setConfirmingDelete(false)}>
              Cancel
            </button>
          </div>
        ) : (
          <div className="form-actions">
            <button type="button" className="btn-danger" onClick={() => setConfirmingDelete(true)}>
              Delete Account
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Settings;
