import { useEffect, useState } from "react";

import { IconBell, IconCheck, IconTrash } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import {
  deleteNotification,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../services/api";

function timeAgo(isoString) {
  const then = new Date(isoString.replace(" ", "T") + (isoString.endsWith("Z") ? "" : "Z"));
  const seconds = Math.floor((Date.now() - then.getTime()) / 1000);
  if (Number.isNaN(seconds)) return isoString;
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function Notifications() {
  const { token } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  function refresh() {
    setLoading(true);
    return getNotifications(token)
      .then(setNotifications)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleMarkRead(id) {
    await markNotificationRead(id, token).catch((err) => setError(err.message));
    await refresh();
  }

  async function handleMarkAllRead() {
    await markAllNotificationsRead(token).catch((err) => setError(err.message));
    await refresh();
  }

  async function handleDelete(id) {
    await deleteNotification(id, token).catch((err) => setError(err.message));
    await refresh();
  }

  const hasUnread = notifications.some((n) => !n.is_read);

  return (
    <div className="page">
      <div className="page-header dashboard-header">
        <div>
          <h1>Notifications</h1>
          <p>Budget alerts and bill reminders land here.</p>
        </div>
        {hasUnread && (
          <button type="button" className="btn-secondary" onClick={handleMarkAllRead}>
            <IconCheck width={16} height={16} />
            Mark all as read
          </button>
        )}
      </div>

      {error && <p className="error-message">{error}</p>}

      {loading ? (
        <p className="loading-state">Loading notifications...</p>
      ) : notifications.length === 0 ? (
        <div className="card empty-state">
          <IconBell width={36} height={36} />
          <p>You're all caught up — no notifications yet.</p>
        </div>
      ) : (
        <div className="card">
          {notifications.map((n) => (
            <div key={n.id} className={`notification-row${n.is_read ? "" : " unread"}`}>
              <span className={`notification-dot ${n.type}`} />
              <div className="notification-main">
                <div className="notification-title">{n.title}</div>
                {n.message && <div className="notification-message">{n.message}</div>}
                <div className="notification-time">{timeAgo(n.created_at)}</div>
              </div>
              <div className="row-actions">
                {!n.is_read && (
                  <button
                    type="button"
                    className="btn-icon"
                    title="Mark as read"
                    onClick={() => handleMarkRead(n.id)}
                  >
                    <IconCheck width={16} height={16} />
                  </button>
                )}
                <button
                  type="button"
                  className="btn-icon danger"
                  title="Delete"
                  onClick={() => handleDelete(n.id)}
                >
                  <IconTrash width={16} height={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Notifications;
