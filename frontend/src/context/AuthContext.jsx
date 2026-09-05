import { createContext, useContext, useEffect, useState } from "react";

import {
  getCurrentUser,
  loginUser,
  loginWithFacebook as apiLoginWithFacebook,
  loginWithFirebase as apiLoginWithFirebase,
  loginWithGoogle as apiLoginWithGoogle,
  logoutUser,
  registerUser,
  updateProfile as apiUpdateProfile,
  updateSettings as apiUpdateSettings,
} from "../services/api";

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

  // The stored user is a snapshot from whenever you last logged in, so any
  // field changed server-side since then (currency, name, admin flag, whether
  // the account was suspended) stayed stale until the next login — which is
  // why amounts kept rendering in the old currency. Re-fetch once on mount so
  // the cache is only ever a fast first paint, not the source of truth.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getCurrentUser(token)
      .then((data) => {
        const fresh = data.user ?? data;
        if (cancelled || !fresh) return;
        localStorage.setItem("user", JSON.stringify(fresh));
        setAuth((prev) => ({ ...prev, user: fresh }));
      })
      // Offline or a hiccup: keep showing the cached user rather than
      // bouncing someone out of a working session. A genuinely dead token
      // gets rejected by the next real request anyway.
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function loginWithFirebaseToken(idToken) {
    const data = await apiLoginWithFirebase(idToken);
    persist(data.token, data.user);
  }

  // Email/password always goes through this app's own backend, never Firebase,
  // even when Firebase is configured. Firebase is used ONLY for the Google
  // popup (see SocialAuthButtons), which matches an existing account by email.
  //
  // Routing email/password through Firebase instead used to look tidy, but it
  // silently locked out every account that already existed: those passwords are
  // hashed in our own users table and were never created in Firebase, so
  // Firebase answered auth/invalid-credential for all of them. Keeping one
  // credential store also keeps Profile's "change password" meaningful — it
  // writes to our DB, which would not be the store Firebase checked.
  async function login(email, password) {
    const data = await loginUser({ email, password });
    persist(data.token, data.user);
  }

  async function register(name, email, password) {
    const data = await registerUser({ name, email, password });
    persist(data.token, data.user);
  }

  async function loginWithGoogle(accessToken) {
    const data = await apiLoginWithGoogle(accessToken);
    persist(data.token, data.user);
  }

  async function loginWithFacebook(accessToken) {
    const data = await apiLoginWithFacebook(accessToken);
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

  async function updateProfile(data) {
    const result = await apiUpdateProfile(data, token);
    localStorage.setItem("user", JSON.stringify(result.user));
    setAuth((prev) => ({ ...prev, user: result.user }));
    return result;
  }

  async function updateSettings(data) {
    const result = await apiUpdateSettings(data, token);
    localStorage.setItem("user", JSON.stringify(result.user));
    setAuth((prev) => ({ ...prev, user: result.user }));
    return result;
  }

  const value = {
    token,
    user,
    isAuthenticated: Boolean(token),
    login,
    register,
    loginWithGoogle,
    loginWithFacebook,
    loginWithFirebaseToken,
    logout,
    updateProfile,
    updateSettings,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook so components just call useAuth() instead of importing
// useContext + AuthContext everywhere.
export function useAuth() {
  return useContext(AuthContext);
}
