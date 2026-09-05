import { useEffect, useRef } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { logPageView } from "./services/api";
import { loadRates } from "./utils/fx";
import Accounts from "./pages/Accounts";
import Bills from "./pages/Bills";
import Budgets from "./pages/Budgets";
import Categories from "./pages/Categories";
import Dashboard from "./pages/Dashboard";
import Goals from "./pages/Goals";
import Login from "./pages/Login";
import Notifications from "./pages/Notifications";
import Profile from "./pages/Profile";
import Recurring from "./pages/Recurring";
import Register from "./pages/Register";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Transactions from "./pages/Transactions";

// Wraps a page so it's only reachable when logged in; otherwise bounce to /login.
function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

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
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
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

// The sidebar layout only makes sense once logged in; logged-out pages
// (login/register) get a plain top bar instead of a side-by-side shell.
function Layout() {
  const { isAuthenticated } = useAuth();
  usePageViewTracking();

  if (!isAuthenticated) {
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
      <AuthProvider>
        <Layout />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
