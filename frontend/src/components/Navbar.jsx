import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import Avatar from "./Avatar";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../hooks/useTheme";
import ThemeSwitch from "./ThemeSwitch";
import {
  IconBarChart,
  IconDashboard,
  IconLogout,
  IconMenu,
  IconTarget,
  IconTransactions,
  IconUser,
  IconWallet,
  IconX,
} from "./icons";

function BrandMark() {
  return (
    <span className="brand-mark">
      <IconWallet width={17} height={17} />
    </span>
  );
}

function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  if (!isAuthenticated) {
    return (
      <nav className="public-nav">
        <Link to="/login" className="public-nav-brand">
          <BrandMark />
          <span>Expense Tracker</span>
        </Link>
        <div className="public-nav-links">
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
          <span style={{ marginLeft: "1.25rem", display: "inline-flex" }}>
            <ThemeSwitch theme={theme} onToggle={toggleTheme} />
          </span>
        </div>
      </nav>
    );
  }

  const links = [
    { to: "/", label: "Dashboard", icon: IconDashboard },
    { to: "/transactions", label: "Transactions", icon: IconTransactions },
    { to: "/reports", label: "Reports", icon: IconBarChart },
    { to: "/budgets", label: "Budgets", icon: IconTarget },
    { to: "/profile", label: "Profile", icon: IconUser },
  ];

  return (
    <>
      <div className="mobile-topbar">
        <button
          type="button"
          className="mobile-menu-btn"
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
        >
          <IconMenu />
        </button>
        <Link to="/" className="sidebar-brand">
          <BrandMark />
          <span>Expense Tracker</span>
        </Link>
      </div>

      {mobileOpen && <div className="sidebar-backdrop" onClick={() => setMobileOpen(false)} />}

      <aside className={`sidebar${mobileOpen ? " sidebar-open" : ""}`}>
        <div className="sidebar-brand-section">
          <Link to="/" className="sidebar-brand">
            <BrandMark />
            <span>Expense Tracker</span>
          </Link>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <IconX width={18} height={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {links.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`sidebar-link${location.pathname === to ? " active" : ""}`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon width={18} height={18} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <Link to="/profile" className="sidebar-user" onClick={() => setMobileOpen(false)}>
            <Avatar user={user} size={30} />
            <span>{user.name}</span>
          </Link>
          <div className="sidebar-theme-row">
            <span>{theme === "dark" ? "Dark mode" : "Light mode"}</span>
            <ThemeSwitch theme={theme} onToggle={toggleTheme} />
          </div>
          <button className="sidebar-logout" onClick={handleLogout}>
            <IconLogout width={18} height={18} />
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}

export default Navbar;
