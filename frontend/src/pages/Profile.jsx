import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import Avatar from "../components/Avatar";
import { IconCamera, IconLogout } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import { DEFAULT_CURRENCY } from "../utils/currency";

const MAX_FILE_BYTES = 2 * 1024 * 1024; // 2MB, matches the backend cap

// Backend stores timestamps as "YYYY-MM-DD HH:MM:SS", which Safari refuses to
// parse with `new Date(...)`. Reading the date part directly avoids that.
function formatJoined(createdAt) {
  const [y, m, d] = String(createdAt).slice(0, 10).split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    month: "short",
    year: "numeric",
  });
}

function IconSpinner() {
  return <span className="btn-spinner" aria-hidden="true" />;
}

function Profile() {
  const { user, updateProfile, logout } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [loggingOut, setLoggingOut] = useState(false);

  const [name, setName] = useState(user.name);
  const [nameStatus, setNameStatus] = useState(null); // { type: 'success' | 'error', message }

  const [avatarStatus, setAvatarStatus] = useState(null);
  const [avatarUploading, setAvatarUploading] = useState(false);

  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [passwordStatus, setPasswordStatus] = useState(null);

  async function handleNameSubmit(event) {
    event.preventDefault();
    setNameStatus(null);
    try {
      await updateProfile({ name });
      setNameStatus({ type: "success", message: "Name updated." });
    } catch (err) {
      setNameStatus({ type: "error", message: err.message });
    }
  }

  function handleAvatarChange(event) {
    const file = event.target.files[0];
    if (!file) return;

    setAvatarStatus(null);

    if (!file.type.startsWith("image/")) {
      setAvatarStatus({ type: "error", message: "Please choose an image file." });
      return;
    }
    if (file.size > MAX_FILE_BYTES) {
      setAvatarStatus({ type: "error", message: "Image must be 2MB or smaller." });
      return;
    }

    setAvatarUploading(true);
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        await updateProfile({ avatar: reader.result });
        setAvatarStatus({ type: "success", message: "Profile picture updated." });
      } catch (err) {
        setAvatarStatus({ type: "error", message: err.message });
      } finally {
        setAvatarUploading(false);
      }
    };
    reader.onerror = () => {
      setAvatarStatus({ type: "error", message: "Couldn't read that file." });
      setAvatarUploading(false);
    };
    reader.readAsDataURL(file);
  }

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      navigate("/login");
    } finally {
      setLoggingOut(false);
    }
  }

  async function handlePasswordSubmit(event) {
    event.preventDefault();
    setPasswordStatus(null);

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordStatus({ type: "error", message: "New passwords don't match." });
      return;
    }

    try {
      await updateProfile({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPasswordStatus({ type: "success", message: "Password changed." });
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      setPasswordStatus({ type: "error", message: err.message });
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Profile</h1>
        <p>Manage your account details.</p>
      </div>

      <div className="profile-hero card">
        <div className="profile-hero-cover" />
        <div className="profile-hero-body">
          <button
            type="button"
            className="profile-avatar-btn"
            onClick={() => fileInputRef.current.click()}
            disabled={avatarUploading}
            aria-label="Change profile picture"
          >
            <Avatar user={user} size={88} />
            <span className="profile-avatar-overlay">
              {avatarUploading ? <IconSpinner /> : <IconCamera width={18} height={18} />}
            </span>
          </button>

          <div className="profile-hero-meta">
            <h2>{user.name}</h2>
            <p>{user.email}</p>
            <div className="profile-badges">
              {user.is_admin && <span className="profile-badge accent">Admin</span>}
              <span className="profile-badge">{user.currency || DEFAULT_CURRENCY}</span>
              {user.created_at && (
                <span className="profile-badge muted">
                  Joined {formatJoined(user.created_at)}
                </span>
              )}
            </div>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleAvatarChange}
          hidden
        />
        {avatarStatus && (
          <p
            className={`profile-hero-status ${
              avatarStatus.type === "error" ? "error-message" : "success-message"
            }`}
          >
            {avatarStatus.message}
          </p>
        )}
      </div>

      <div className="profile-grid">
        <div className="card card-padded">
          <div className="profile-card-head">
            <h2 className="card-title">Personal details</h2>
            <p>The name shown across your account.</p>
          </div>
          {nameStatus && (
            <p className={nameStatus.type === "error" ? "error-message" : "success-message"}>
              {nameStatus.message}
            </p>
          )}
          <form onSubmit={handleNameSubmit}>
            <label>
              Full name
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              Email
              {/* Read-only: the address is the account identity and is also
                  what Google sign-in matches on, so it isn't editable here. */}
              <input type="email" value={user.email} disabled />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={name.trim() === user.name}>
                Save changes
              </button>
            </div>
          </form>
        </div>

        <div className="card card-padded">
          <div className="profile-card-head">
            <h2 className="card-title">Password</h2>
            <p>Use at least 6 characters.</p>
          </div>
          {passwordStatus && (
            <p className={passwordStatus.type === "error" ? "error-message" : "success-message"}>
              {passwordStatus.message}
            </p>
          )}
          <form onSubmit={handlePasswordSubmit}>
            <label>
              Current password
              <input
                type="password"
                value={passwordForm.current_password}
                onChange={(e) =>
                  setPasswordForm((prev) => ({ ...prev, current_password: e.target.value }))
                }
                required
              />
            </label>
            <label>
              New password
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) =>
                  setPasswordForm((prev) => ({ ...prev, new_password: e.target.value }))
                }
                required
                minLength={6}
              />
            </label>
            <label>
              Confirm new password
              <input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) =>
                  setPasswordForm((prev) => ({ ...prev, confirm_password: e.target.value }))
                }
                required
                minLength={6}
              />
            </label>
            <div className="form-actions">
              <button type="submit">Update password</button>
            </div>
          </form>
        </div>

        <div className="card card-padded profile-signout">
          <div className="profile-card-head">
            <h2 className="card-title">Sign out</h2>
            <p>You'll be signed out on this device and returned to the login page.</p>
          </div>
          <div className="form-actions">
            <button
              type="button"
              className="btn-danger"
              onClick={handleLogout}
              disabled={loggingOut}
            >
              <IconLogout width={18} height={18} />
              {loggingOut ? "Signing out..." : "Logout"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
