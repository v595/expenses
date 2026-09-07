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
  verifyTwoFactor as apiVerifyTwoFactor,
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

  function clearSession() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setAuth({ token: null, user: null });
  }

  // A dead token (expired, revoked, or pointing at a user that no longer
  // exists) used to leave the app "logged in" — the token stayed cached, so
  // every page kept fetching, kept getting 401 "Authentication required",
  // and kept showing that same error banner with no way out but a manual
  // logout. api.js fires this event the moment any authenticated request
  // gets rejected; clearing the session here sends the user back to /login
  // (via RequireAuth) instead of leaving them stuck.
  useEffect(() => {
    function onUnauthorized() {
      clearSession();
    }
    window.addEventListener("auth:unauthorized", onUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", onUnauthorized);
  }, []);

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

  // Every login path can come back either as a completed session (token +
  // user) or, when the account has 2FA turned on, a { requires_two_factor,
  // ticket } stub — the caller (Login page) shows a code-entry step and
  // finishes with verifyTwoFactor(ticket, code) instead of persisting here.
  function settleSession(data) {
    if (data.requires_two_factor) return data;
    persist(data.token, data.user);
    return data;
  }

  async function verifyTwoFactor(ticket, code) {
    const data = await apiVerifyTwoFactor(ticket, code);
    return settleSession(data);
  }

  async function loginWithFirebaseToken(idToken) {
    const data = await apiLoginWithFirebase(idToken);
    return settleSession(data);
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
    return settleSession(data);
  }

  async function register(name, email, password) {
    const data = await registerUser({ name, email, password });
    return settleSession(data);
  }

  async function loginWithGoogle(accessToken) {
    const data = await apiLoginWithGoogle(accessToken);
    return settleSession(data);
  }

  async function loginWithFacebook(accessToken) {
    const data = await apiLoginWithFacebook(accessToken);
    return settleSession(data);
  }

  async function logout() {
    if (token) {
      await logoutUser(token).catch(() => {}); // best-effort; log out locally regardless
    }
    clearSession();
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

  // For flows that update the user server-side outside updateProfile/Settings
  // (e.g. enabling/disabling 2FA) but still need the cached user refreshed.
  function setUser(nextUser) {
    localStorage.setItem("user", JSON.stringify(nextUser));
    setAuth((prev) => ({ ...prev, user: nextUser }));
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
    verifyTwoFactor,
    logout,
    updateProfile,
    updateSettings,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook so components just call useAuth() instead of importing
// useContext + AuthContext everywhere.
export function useAuth() {
  return useContext(AuthContext);
}
