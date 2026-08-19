import { createContext, useContext, useState } from "react";

import { loginUser, logoutUser, registerUser } from "../services/api";

const AuthContext = createContext(null);

// Read any previously saved session so refreshing the page doesn't log you out.
function loadStoredAuth() {
  const token = localStorage.getItem("token");
  const userJson = localStorage.getItem("user");
  if (!token || !userJson) return { token: null, user: null };
  return { token, user: JSON.parse(userJson) };
}

export function AuthProvider({ children }) {
  const [{ token, user }, setAuth] = useState(loadStoredAuth);

  function persist(token, user) {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    setAuth({ token, user });
  }

  async function login(email, password) {
    const data = await loginUser({ email, password });
    persist(data.token, data.user);
  }

  async function register(name, email, password) {
    const data = await registerUser({ name, email, password });
    persist(data.token, data.user);
  }

  async function logout() {
    if (token) {
      await logoutUser(token).catch(() => {}); // best-effort; log out locally regardless
    }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setAuth({ token: null, user: null });
  }

  const value = { token, user, isAuthenticated: Boolean(token), login, register, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook so components just call useAuth() instead of importing
// useContext + AuthContext everywhere.
export function useAuth() {
  return useContext(AuthContext);
}
