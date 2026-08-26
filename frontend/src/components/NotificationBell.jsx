import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getNotifications, getUnreadNotificationCount, markAllNotificationsRead } from "../services/api";
import { IconBell, IconCheck } from "./icons";

const POLL_INTERVAL_MS = 60_000;

function NotificationBell() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(0);
  const [preview, setPreview] = useState([]);
  const wrapRef = useRef(null);

  function refreshCount() {
    getUnreadNotificationCount(token)
      .then((data) => setCount(data.count))
      .catch(() => {});
  }

  useEffect(() => {
    refreshCount();
    const interval = setInterval(refreshCount, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapRef.current && !wrapRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleToggle() {
    if (!open) {
      getNotifications(token)
        .then((data) => setPreview(data.slice(0, 5)))
        .catch(() => {});
    }
    setOpen((o) => !o);
  }

  async function handleMarkAllRead(event) {
    event.stopPropagation();
    await markAllNotificationsRead(token).catch(() => {});
    setPreview((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setCount(0);
  }

  return (
    <div className="notification-bell-wrap" ref={wrapRef}>
      <button
        type="button"
        className="btn-icon notification-bell-btn"
        onClick={handleToggle}
        aria-label="Notifications"
      >
        <IconBell width={19} height={19} />
        {count > 0 && <span className="notification-badge">{count > 9 ? "9+" : count}</span>}
      </button>

      {open && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <span>Notifications</span>
            {count > 0 && (
              <button type="button" className="btn-icon" title="Mark all as read" onClick={handleMarkAllRead}>
                <IconCheck width={15} height={15} />
              </button>
            )}
          </div>
          {preview.length === 0 ? (
            <p className="notification-dropdown-empty">No notifications yet.</p>
          ) : (
            <ul className="notification-dropdown-list">
              {preview.map((n) => (
                <li key={n.id} className={n.is_read ? "" : "unread"}>
                  <span className={`notification-dot ${n.type}`} />
                  <div>
                    <div className="notification-title">{n.title}</div>
                    {n.message && <div className="notification-message">{n.message}</div>}
                  </div>
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="notification-dropdown-viewall"
            onClick={() => {
              setOpen(false);
              navigate("/notifications");
            }}
          >
            View all notifications
          </button>
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
