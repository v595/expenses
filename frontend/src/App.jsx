import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Navbar from "./components/Navbar";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Budgets from "./pages/Budgets";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Recurring from "./pages/Recurring";
import Register from "./pages/Register";
import Reports from "./pages/Reports";
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

// The sidebar layout only makes sense once logged in; logged-out pages
// (login/register) get a plain top bar instead of a side-by-side shell.
function Layout() {
  const { isAuthenticated } = useAuth();

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
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
