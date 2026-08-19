import { useRef, useState } from "react";

import Avatar from "../components/Avatar";
import { useAuth } from "../context/AuthContext";

const MAX_FILE_BYTES = 2 * 1024 * 1024; // 2MB, matches the backend cap

function Profile() {
  const { user, updateProfile } = useAuth();
  const fileInputRef = useRef(null);

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

      <div className="dashboard-grid">
        <div className="card card-padded">
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
            <Avatar user={user} size={56} />
            <div>
              <div style={{ fontWeight: 700 }}>{user.name}</div>
              <div style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>{user.email}</div>
            </div>
          </div>

          {avatarStatus && (
            <p className={avatarStatus.type === "error" ? "error-message" : "success-message"}>
              {avatarStatus.message}
            </p>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleAvatarChange}
            style={{ display: "none" }}
          />
          <div className="form-actions" style={{ marginBottom: "1.5rem" }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => fileInputRef.current.click()}
              disabled={avatarUploading}
            >
              {avatarUploading ? "Uploading..." : "Change Picture"}
            </button>
          </div>

          <h2 className="card-title">Name</h2>
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
            <div className="form-actions">
              <button type="submit">Save Name</button>
            </div>
          </form>
        </div>

        <div className="card card-padded">
          <h2 className="card-title">Change Password</h2>
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
              <button type="submit">Change Password</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Profile;
