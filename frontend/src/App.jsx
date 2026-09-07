import { useEffect, useRef } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar";
import { AppInfoProvider } from "./context/AppInfoContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { logPageView } from "./services/api";
import { loadRates } from "./utils/fx";
import Accounts from "./pages/Accounts";
import Bills from "./pages/Bills";
import Budgets from "./pages/Budgets";
import Cashbook from "./pages/Cashbook";
import Categories from "./pages/Categories";
import Dashboard from "./pages/Dashboard";
import DebtPayoff from "./pages/DebtPayoff";
import ForgotPassword from "./pages/ForgotPassword";
import Goals from "./pages/Goals";
import Ledger from "./pages/Ledger";
import Login from "./pages/Login";
import Notifications from "./pages/Notifications";
import PartyDetail from "./pages/PartyDetail";
import Profile from "./pages/Profile";
import Recurring from "./pages/Recurring";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Transactions from "./pages/Transactions";

// Wraps a page so it's only reachable when logged in; otherwise bounce to /login.
function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

// The mirror image of RequireAuth: login/register make no sense once you're
// already signed in, and used to render on top of the sidebar shell instead
// of redirecting — a broken hybrid layout reachable via the back button or a
// stale bookmark. Bounce straight to the dashboard instead.
function RedirectIfAuthed({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/" replace /> : children;
}

// Routes that are never wrapped in the sidebar shell, even for a signed-in
// visitor — e.g. someone logged in on desktop who opens a password-reset
// link from email is still allowed to finish that flow, just without the
// sidebar rendering underneath it.
const PLAIN_LAYOUT_PATHS = ["/login", "/register", "/forgot-password", "/reset-password"];

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/transactions"
        element={
          <RequireAuth>
            <Transactions />
          </RequireAuth>
        }
      />
      <Route
        path="/reports"
        element={
          <RequireAuth>
            <Reports />
          </RequireAuth>
        }
      />
      <Route
        path="/budgets"
        element={
          <RequireAuth>
            <Budgets />
          </RequireAuth>
        }
      />
      <Route
        path="/recurring"
        element={
          <RequireAuth>
            <Recurring />
          </RequireAuth>
        }
      />
      <Route
        path="/accounts"
        element={
          <RequireAuth>
            <Accounts />
          </RequireAuth>
        }
      />
      <Route
        path="/goals"
        element={
          <RequireAuth>
            <Goals />
          </RequireAuth>
        }
      />
      <Route
        path="/bills"
        element={
          <RequireAuth>
            <Bills />
          </RequireAuth>
        }
      />
      <Route
        path="/categories"
        element={
          <RequireAuth>
            <Categories />
          </RequireAuth>
        }
      />
      <Route
        path="/ledger"
        element={
          <RequireAuth>
            <Ledger />
          </RequireAuth>
        }
      />
      <Route
        path="/ledger/:partyId"
        element={
          <RequireAuth>
            <PartyDetail />
          </RequireAuth>
        }
      />
      <Route
        path="/cashbook"
        element={
          <RequireAuth>
            <Cashbook />
          </RequireAuth>
        }
      />
      <Route
        path="/debt-payoff"
        element={
          <RequireAuth>
            <DebtPayoff />
          </RequireAuth>
        }
      />
      <Route
        path="/notifications"
        element={
          <RequireAuth>
            <Notifications />
          </RequireAuth>
        }
      />
      <Route
        path="/settings"
        element={
          <RequireAuth>
            <Settings />
          </RequireAuth>
        }
      />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <Profile />
          </RequireAuth>
        }
      />
      <Route
        path="/login"
        element={
          <RedirectIfAuthed>
            <Login />
          </RedirectIfAuthed>
        }
      />
      <Route
        path="/register"
        element={
          <RedirectIfAuthed>
            <Register />
          </RedirectIfAuthed>
        }
      />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
    </Routes>
  );
}

// Reports every route change to the backend so admin can see page activity
// per user. Best-effort — a failed ping shouldn't affect navigation at all.
function usePageViewTracking() {
  const { isAuthenticated, token } = useAuth();
  const location = useLocation();
  const lastPath = useRef(null);

  useEffect(() => {
    if (!isAuthenticated || lastPath.current === location.pathname) return;
    lastPath.current = location.pathname;
    logPageView(location.pathname, token).catch(() => {});
  }, [isAuthenticated, token, location.pathname]);
}

// The sidebar layout only makes sense once logged in, and never on a
// PLAIN_LAYOUT_PATHS route — a signed-in visitor can still land on
// /reset-password (an emailed link) and should see the plain auth card, not
// the sidebar shell rendered underneath it.
function Layout() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  usePageViewTracking();

  const isPlainLayout = !isAuthenticated || PLAIN_LAYOUT_PATHS.includes(location.pathname);

  if (isPlainLayout) {
    return (
      <>
        <Navbar />
        <AppRoutes />
      </>
    );
  }

  return (
    <div className="app-shell">
      <Navbar />
      <div className="main-content">
        <AppRoutes />
      </div>
    </div>
  );
}

function App() {
  // Warm the FX table once at startup so the first render of any amount
  // already has real rates rather than the offline fallback.
  useEffect(() => {
    loadRates();
  }, []);

  return (
    <BrowserRouter>
      <AppInfoProvider>
        <AuthProvider>
          <Layout />
        </AuthProvider>
      </AppInfoProvider>
    </BrowserRouter>
  );
}

export default App;
